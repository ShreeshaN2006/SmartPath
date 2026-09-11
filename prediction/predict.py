#!/usr/bin/env python3
"""
DCRNN Inference Script
----------------------
Predicts Average Speed for each traffic node using the trained DCRNN model.

Usage:
    python prediction/predict.py --horizon 1
    python prediction/predict.py --horizon 3
    python prediction/predict.py --horizon 7 --output custom_predictions.csv
"""

import argparse
import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path

from training.preprocessing import prepare_data, create_complete_dataset, split_data_chronological, create_sequences
from training.dcrnn import DCRNN, load_chebyshev_polys
from training.graph import load_adjacency_matrix


def load_model_and_metadata(model_path: str, device: torch.device):
    """Load trained model and metadata."""
    checkpoint = torch.load(model_path, map_location=device)
    config = checkpoint['config']

    # Ensure output_dim is in config (default to 1 for backward compatibility)
    if 'output_dim' not in config:
        config['output_dim'] = 1

    # Load adjacency and Chebyshev polynomials
    adj = load_adjacency_matrix('data/traffic/adjacency_matrix.csv')
    cheb_polys = load_chebyshev_polys(adj, config['K'], device)

    # Create model
    model = DCRNN(
        input_dim=config['input_dim'],
        hidden_dim=config['hidden_dim'],
        num_layers=config['num_layers'],
        output_dim=config['output_dim'],
        horizon=config['horizon'],
        K=config['K'],
        cheb_polys=cheb_polys
    ).to(device)

    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    return model, config


def load_scalers_and_metadata():
    """Load scalers and metadata."""
    feature_scaler = joblib.load('models/scalers/feature_scaler.pkl')
    target_scaler = joblib.load('models/scalers/target_scaler.pkl')
    feature_cols = joblib.load('models/scalers/feature_cols.pkl')
    node_names = joblib.load('models/scalers/node_names.pkl')
    encoders = joblib.load('models/scalers/categorical_encoders.pkl')
    return feature_scaler, target_scaler, feature_cols, node_names, encoders


def prepare_latest_sequence(horizon: int, feature_cols: list, node_names: list,
                           encoders: dict, feature_scaler) -> tuple:
    """
    Prepare the latest input sequence for prediction.
    Uses the most recent data from the dataset.
    """
    # Load full dataset
    df = pd.read_csv('data/traffic/smartpath_traffic_model_ready.csv')
    df['Date'] = pd.to_datetime(df['Date'])

    # Select and prepare features
    df = df.drop(columns=[c for c in ['Travel Time Index', 'Road Capacity Utilization',
                                       'speed_lag_2d', 'volume_lag_2d', 'congestion_lag_2d',
                                       'speed_lag_3d', 'volume_lag_3d', 'congestion_lag_3d',
                                       'speed_lag_7d', 'volume_lag_7d', 'congestion_lag_7d',
                                       'quarter'] if c in df.columns], errors='ignore')

    lag_cols = [c for c in df.columns if 'lag_' in c or 'rolling_' in c]
    for col in lag_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Encode categoricals
    from sklearn.preprocessing import LabelEncoder
    for col in ['Weather Conditions', 'Roadwork and Construction Activity']:
        if col in df.columns:
            if col in encoders:
                le = encoders[col]
                df[col] = df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            else:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))

    # Create complete dataset with forward fill
    X_all, _, complete_dates = create_complete_dataset(
        df, feature_cols, 'Average Speed', node_names
    )

    # Scale using fitted scaler
    n_dates, n_nodes, n_features = X_all.shape
    X_flat = X_all.reshape(-1, n_features)
    X_scaled = feature_scaler.transform(X_flat).reshape(n_dates, n_nodes, n_features)

    return X_scaled, complete_dates


def predict(model, X_seq: np.ndarray, target_scaler, horizon: int, device: torch.device) -> np.ndarray:
    """Generate predictions."""
    model.eval()
    with torch.no_grad():
        x = torch.from_numpy(X_seq).float().to(device)
        out = model(x, teacher_forcing_ratio=0.0)  # (batch, horizon, nodes, 1)
        out = out.squeeze(-1).cpu().numpy()  # (batch, horizon, nodes)

    # Inverse transform
    batch, h, nodes = out.shape
    out_flat = out.reshape(-1, 1)
    out_orig = target_scaler.inverse_transform(out_flat).reshape(batch, h, nodes)

    return out_orig


def save_predictions(predictions: np.ndarray, node_names: list, complete_dates,
                     horizon: int, output_path: str):
    """Save predictions to CSV."""
    # predictions shape: (batch, horizon, nodes)
    # Use the last batch for latest predictions
    latest_preds = predictions[-1]  # (horizon, nodes)

    rows = []
    for h in range(horizon):
        pred_date = complete_dates[-len(predictions) + h] if len(complete_dates) > len(predictions) else None
        for i, node in enumerate(node_names):
            rows.append({
                'prediction_date': pred_date,
                'horizon_day': h + 1,
                'node_id': i,
                'Road/Intersection Name': node,
                'predicted_average_speed': latest_preds[h, i]
            })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")
    return df


def main():
    parser = argparse.ArgumentParser(description='DCRNN Traffic Speed Prediction')
    parser.add_argument('--horizon', type=int, default=1, help='Prediction horizon (days)')
    parser.add_argument('--model', type=str, default='models/dcrnn/best_model.pt',
                        help='Path to model checkpoint')
    parser.add_argument('--output', type=str, default='predictions/latest_speed_predictions.csv',
                        help='Output CSV path')
    parser.add_argument('--device', type=str, default='auto',
                        help='Device (auto/cpu/cuda)')
    args = parser.parse_args()

    # Device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    print(f"Using device: {device}")

    # Load model
    print(f"Loading model from {args.model}...")
    model, config = load_model_and_metadata(args.model, device)

    # Load scalers and metadata
    feature_scaler, target_scaler, feature_cols, node_names, encoders = load_scalers_and_metadata()

    # Prepare latest sequence
    print("Preparing latest input sequence...")
    X_scaled, complete_dates = prepare_latest_sequence(
        args.horizon, config['feature_cols'], node_names, encoders, feature_scaler
    )

    # Create sequence for prediction (use last seq_len days)
    seq_len = config['seq_len']
    if len(X_scaled) < seq_len:
        raise ValueError(f"Not enough data: need {seq_len} days, have {len(X_scaled)}")

    X_seq = X_scaled[-seq_len:].reshape(1, seq_len, -1, len(config['feature_cols']))

    # Predict
    print(f"Generating predictions for horizon={args.horizon}...")
    predictions = predict(model, X_seq, joblib.load('models/scalers/target_scaler.pkl'),
                         args.horizon, device)

    # Save
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df = save_predictions(predictions, node_names, complete_dates,
                          args.horizon, args.output)

    # Print summary
    print(f"\nPredictions for next {args.horizon} day(s):")
    for h in range(args.horizon):
        print(f"\nDay {h+1}:")
        for i, node in enumerate(node_names):
            print(f"  {node}: {predictions[0, h, i]:.2f} km/h")


if __name__ == '__main__':
    import pandas as pd
    main()