"""
DCRNN Training Script
---------------------
Trains the DCRNN model with configurable hyperparameters.

Usage:
    python training/train_dcrnn.py \
        --seq-len 7 \
        --horizon 1 \
        --epochs 100 \
        --batch-size 32 \
        --lr 0.001 \
        --hidden-dim 64 \
        --num-layers 2 \
        --K 2
"""

import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time
from tqdm import tqdm

from training.preprocessing import prepare_data
from training.dataset import create_dataloaders
from training.dcrnn import DCRNN, load_chebyshev_polys
from training.evaluation import evaluate_model
from training.graph import load_adjacency_matrix


def parse_args():
    parser = argparse.ArgumentParser(description='Train DCRNN for traffic forecasting')
    parser.add_argument('--seq-len', type=int, default=7, help='Input sequence length (days)')
    parser.add_argument('--horizon', type=int, default=1, help='Prediction horizon (days)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--hidden-dim', type=int, default=64, help='Hidden dimension')
    parser.add_argument('--num-layers', type=int, default=2, help='Number of DCGRU layers')
    parser.add_argument('--K', type=int, default=2, help='Chebyshev polynomial order')
    parser.add_argument('--dropout', type=float, default=0.2, help='Dropout rate')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    parser.add_argument('--lr-scheduler', action='store_true', help='Use learning rate scheduler')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--device', type=str, default='auto', help='Device (auto/cpu/cuda)')
    return parser.parse_args()


def set_seed(seed: int):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_one_epoch(model, loader, optimizer, criterion, device, teacher_forcing_ratio=0.0):
    model.train()
    total_loss = 0
    valid_batches = 0

    for x, y in tqdm(loader, desc='Training', leave=False):
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        out = model(x, teacher_forcing_ratio=teacher_forcing_ratio)
        # out: (batch, horizon, nodes, 1) -> squeeze
        out = out.squeeze(-1)
        loss = criterion(out, y)

        if torch.isnan(loss):
            continue

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * x.size(0)
        valid_batches += 1

    return total_loss / max(valid_batches, 1)


def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    valid_batches = 0

    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x, teacher_forcing_ratio=0.0)
            out = out.squeeze(-1)
            loss = criterion(out, y)

            if torch.isnan(loss):
                continue

            total_loss += loss.item() * x.size(0)
            valid_batches += 1

    return total_loss / max(valid_batches, 1)


def main():
    args = parse_args()
    set_seed(args.seed)

    # Device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    print(f"Using device: {device}")

    # Load data
    print("Loading and preprocessing data...")
    (X_train, y_train, X_val, y_val, X_test, y_test,
     feature_scaler, target_scaler,
     feature_cols, node_names,
     date_splits) = prepare_data(
        'data/traffic/smartpath_traffic_model_ready.csv',
        seq_len=args.seq_len,
        horizon=args.horizon
    )

    # Create dataloaders
    train_loader, val_loader, test_loader = create_dataloaders(
        X_train, y_train, X_val, y_val, X_test, y_test,
        batch_size=args.batch_size
    )

    # Load adjacency and Chebyshev polynomials
    adj = load_adjacency_matrix('data/traffic/adjacency_matrix.csv')
    cheb_polys = load_chebyshev_polys(adj, args.K, device)

    # Create model
    model = DCRNN(
        input_dim=len(feature_cols),
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        output_dim=1,
        horizon=args.horizon,
        K=args.K,
        cheb_polys=cheb_polys
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # LR scheduler
    scheduler = None
    if args.lr_scheduler:
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )

    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    history = []

    Path('models/dcrnn').mkdir(parents=True, exist_ok=True)
    Path('results/plots').mkdir(parents=True, exist_ok=True)

    # Save config
    config = {
        'seq_len': args.seq_len,
        'horizon': args.horizon,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'lr': args.lr,
        'hidden_dim': args.hidden_dim,
        'num_layers': args.num_layers,
        'K': args.K,
        'dropout': args.dropout,
        'input_dim': len(feature_cols),
        'output_dim': 1,
        'num_nodes': len(node_names),
        'feature_cols': feature_cols,
        'target_col': 'Average Speed',
        'train_dates': [str(d) for d in date_splits[0]],
        'val_dates': [str(d) for d in date_splits[1]],
        'test_dates': [str(d) for d in date_splits[2]],
        'graph_construction': 'provisional_area_based',
        'normalization': 'StandardScaler_train_only'
    }
    with open('models/dcrnn/config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\nStarting training for {args.epochs} epochs...")
    print(f"Train samples: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    for epoch in range(1, args.epochs + 1):
        start_time = time.time()

        # Teacher forcing decay
        tf_ratio = max(0.0, 0.5 * (0.95 ** epoch))

        train_loss = train_one_epoch(model, train_loader, optimizer, criterion,
                                     device, teacher_forcing_ratio=tf_ratio)
        val_loss = validate(model, val_loader, criterion, device)

        epoch_time = time.time() - start_time

        if scheduler:
            scheduler.step(val_loss)

        # Logging
        current_lr = optimizer.param_groups[0]['lr']
        history.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'lr': current_lr,
            'time': epoch_time
        })

        print(f"Epoch {epoch:3d}/{args.epochs} | "
              f"Train: {train_loss:.6f} | "
              f"Val: {val_loss:.6f} | "
              f"LR: {current_lr:.6f} | "
              f"Time: {epoch_time:.1f}s", end='')

        # Checkpoint (only if val_loss is valid)
        if not np.isnan(val_loss) and val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'config': config
            }, 'models/dcrnn/best_model.pt')
            print(" * BEST MODEL SAVED")
        else:
            patience_counter += 1
            print()

        # Early stopping
        if patience_counter >= args.patience:
            print(f"\nEarly stopping triggered after {epoch} epochs")
            break

    # Save final model
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_loss': val_loss,
        'config': config
    }, 'models/dcrnn/final_model.pt')

    # Save training history
    history_df = pd.DataFrame(history)
    history_df.to_csv('results/training_history.csv', index=False)

    # Load best model for evaluation (fallback to final if best doesn't exist)
    best_model_path = 'models/dcrnn/best_model.pt'
    final_model_path = 'models/dcrnn/final_model.pt'
    model_path = best_model_path if Path(best_model_path).exists() else final_model_path

    print(f"\nLoading model from {model_path} for evaluation...")
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])

    # Evaluate on test set
    print("\nEvaluating on test set...")
    overall, per_node, per_horizon = evaluate_model(
        model, test_loader, device, target_scaler, node_names
    )

    print(f"\nTest Metrics:")
    print(f"  MAE:  {overall['MAE']:.4f}")
    print(f"  RMSE: {overall['RMSE']:.4f}")
    print(f"  MAPE: {overall['MAPE']:.2f}%")
    print(f"  R²:   {overall['R2']:.4f}")

    # Save results
    per_node.to_csv('results/dcrnn_per_node.csv', index=False)
    per_horizon.to_csv('results/dcrnn_per_horizon.csv', index=False)

    # Save overall metrics
    results_df = pd.DataFrame([{
        'model': 'DCRNN',
        'seq_len': args.seq_len,
        'horizon': args.horizon,
        'MAE': overall['MAE'],
        'RMSE': overall['RMSE'],
        'MAPE': overall['MAPE'],
        'R2': overall['R2'],
        'epochs_trained': epoch,
        'best_val_loss': best_val_loss
    }])
    results_df.to_csv('results/dcrnn_results.csv', index=False)

    # Save predictions
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for x, y in test_loader:
            x = x.to(device)
            out = model(x).squeeze(-1)
            all_preds.append(out.cpu().numpy())
            all_targets.append(y.cpu().numpy())

    y_pred = np.concatenate(all_preds, axis=0)
    y_true = np.concatenate(all_targets, axis=0)

    # Inverse transform
    y_pred_orig = target_scaler.inverse_transform(y_pred.reshape(-1, 1)).reshape(y_pred.shape)
    y_true_orig = target_scaler.inverse_transform(y_true.reshape(-1, 1)).reshape(y_true.shape)

    np.savez('results/dcrnn_predictions.npz',
             y_pred=y_pred_orig, y_true=y_true_orig)

    print("\nTraining complete!")
    print(f"Best model saved to models/dcrnn/best_model.pt")
    print(f"Results saved to results/")


if __name__ == '__main__':
    main()