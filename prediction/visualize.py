"""
Visualization Script
--------------------
Generates research-quality plots for DCRNN training and evaluation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import joblib
from pathlib import Path

Path('results/plots').mkdir(parents=True, exist_ok=True)


def plot_training_history():
    """Plot training vs validation loss."""
    if not Path('results/training_history.csv').exists():
        print("No training history found")
        return

    df = pd.read_csv('results/training_history.csv')

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(df['epoch'], df['train_loss'], 'b-', label='Train Loss', linewidth=2)
    ax1.plot(df['epoch'], df['val_loss'], 'r-', label='Validation Loss', linewidth=2)
    ax1.set_xlabel('Epoch', fontsize=12)
    ax1.set_ylabel('MSE Loss', fontsize=12)
    ax1.set_title('DCRNN Training History', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    ax2 = ax1.twinx()
    ax2.plot(df['epoch'], df['lr'], 'g--', label='Learning Rate', alpha=0.7)
    ax2.set_ylabel('Learning Rate', fontsize=12)
    ax2.legend(loc='upper right', fontsize=11)

    plt.tight_layout()
    plt.savefig('results/plots/training_history.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved training_history.png")


def plot_actual_vs_predicted():
    """Plot actual vs predicted values for test set."""
    # Load DCRNN predictions
    dcrnn_data = np.load('results/dcrnn_predictions.npz')
    y_pred = dcrnn_data['y_pred']
    y_true = dcrnn_data['y_true']

    # Flatten for overall scatter
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Scatter plot
    ax = axes[0]
    ax.scatter(y_true_flat, y_pred_flat, alpha=0.5, s=10, c='blue', edgecolors='none')
    min_val = min(y_true_flat.min(), y_pred_flat.min())
    max_val = max(y_true_flat.max(), y_pred_flat.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    ax.set_xlabel('Actual Average Speed (km/h)', fontsize=12)
    ax.set_ylabel('Predicted Average Speed (km/h)', fontsize=12)
    ax.set_title('Actual vs Predicted (All Nodes)', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')

    # Residuals
    ax = axes[1]
    residuals = y_pred_flat - y_true_flat
    ax.scatter(y_true_flat, residuals, alpha=0.5, s=10, c='red', edgecolors='none')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('Actual Average Speed (km/h)', fontsize=12)
    ax.set_ylabel('Residual (km/h)', fontsize=12)
    ax.set_title('Residuals vs Actual', fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/plots/actual_vs_predicted.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved actual_vs_predicted.png")


def plot_per_node_metrics():
    """Plot per-node MAE and RMSE for all models."""
    models = ['HistoricalMean', 'NaivePreviousDay', 'Ridge', 'RandomForest', 'XGBoost', 'DCRNN']
    metrics = ['MAE', 'RMSE']

    fig, axes = plt.subplots(len(metrics), 1, figsize=(14, 10))

    x = np.arange(16)
    width = 0.12

    for m_idx, metric in enumerate(metrics):
        ax = axes[m_idx]

        for i, model in enumerate(models):
            try:
                df = pd.read_csv(f'results/baseline_{model}_per_node.csv')
                if model == 'DCRNN':
                    df = pd.read_csv('results/dcrnn_per_node.csv')
            except:
                continue

            values = df[metric].values
            if len(values) == 16:
                offset = (i - len(models)/2 + 0.5) * width
                ax.bar(x + offset, values, width, label=model, alpha=0.8)

        ax.set_xlabel('Node', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'Per-Node {metric} Comparison', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels([f'N{i}' for i in range(16)], rotation=45, ha='right', fontsize=9)
        ax.legend(fontsize=9, ncol=3)
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('results/plots/per_node_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved per_node_comparison.png")


def plot_per_horizon_metrics():
    """Plot per-horizon metrics."""
    models = ['HistoricalMean', 'NaivePreviousDay', 'Ridge', 'RandomForest', 'XGBoost', 'DCRNN']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for m_idx, metric in enumerate(['MAE', 'RMSE', 'MAPE', 'R2']):
        ax = axes[m_idx]

        for model in models:
            try:
                df = pd.read_csv(f'results/baseline_{model}_per_horizon.csv')
                if model == 'DCRNN':
                    df = pd.read_csv('results/dcrnn_per_horizon.csv')
            except:
                continue

            ax.plot(df['horizon'], df[metric], 'o-', label=model, linewidth=2, markersize=6)

        ax.set_xlabel('Prediction Horizon (days)', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'{metric} vs Horizon', fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/plots/per_horizon_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved per_horizon_comparison.png")


def plot_model_comparison():
    """Plot overall model comparison bar chart."""
    df = pd.read_csv('results/model_comparison.csv')

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    models = df['Model'].values
    colors = ['skyblue', 'lightcoral', 'lightgreen', 'gold', 'plum', 'lightsteelblue']

    for idx, metric in enumerate(['MAE', 'RMSE', 'MAPE', 'R2']):
        ax = axes[idx]
        values = df[metric].values
        bars = ax.bar(models, values, color=colors, edgecolor='black', linewidth=0.5)

        # Highlight DCRNN
        dcrnn_idx = list(models).index('DCRNN')
        bars[dcrnn_idx].set_color('red')
        bars[dcrnn_idx].set_edgecolor('darkred')
        bars[dcrnn_idx].set_linewidth(2)

        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'Model Comparison: {metric}', fontsize=14)
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig('results/plots/model_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved model_comparison.png")


def plot_prediction_examples():
    """Plot example predictions for a few nodes."""
    dcrnn_data = np.load('results/dcrnn_predictions.npz')
    y_pred = dcrnn_data['y_pred']
    y_true = dcrnn_data['y_true']

    node_names = joblib.load('models/scalers/node_names.pkl')

    # Plot first 6 nodes
    n_nodes = min(6, y_true.shape[2])
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for i in range(n_nodes):
        ax = axes[i]
        # Show last 50 predictions
        n_show = min(50, y_true.shape[0])
        t = np.arange(n_show)
        ax.plot(t, y_true[-n_show:, 0, i], 'b-', label='Actual', linewidth=1.5, alpha=0.8)
        ax.plot(t, y_pred[-n_show:, 0, i], 'r--', label='Predicted', linewidth=1.5, alpha=0.8)
        ax.set_title(node_names[i], fontsize=11)
        ax.set_xlabel('Time Step', fontsize=10)
        ax.set_ylabel('Speed (km/h)', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/plots/prediction_examples.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved prediction_examples.png")


def plot_error_distribution():
    """Plot prediction error distribution."""
    dcrnn_data = np.load('results/dcrnn_predictions.npz')
    y_pred = dcrnn_data['y_pred']
    y_true = dcrnn_data['y_true']

    errors = (y_pred - y_true).flatten()
    abs_errors = np.abs(errors)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Error distribution
    axes[0].hist(errors, bins=50, density=True, alpha=0.7, color='blue', edgecolor='black')
    axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2)
    axes[0].set_xlabel('Error (km/h)', fontsize=12)
    axes[0].set_ylabel('Density', fontsize=12)
    axes[0].set_title('Prediction Error Distribution', fontsize=14)
    axes[0].grid(True, alpha=0.3)

    # Absolute error distribution
    axes[1].hist(abs_errors, bins=50, density=True, alpha=0.7, color='red', edgecolor='black')
    axes[1].set_xlabel('Absolute Error (km/h)', fontsize=12)
    axes[1].set_ylabel('Density', fontsize=12)
    axes[1].set_title('Absolute Error Distribution', fontsize=14)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/plots/error_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved error_distribution.png")


if __name__ == '__main__':
    print("Generating visualizations...")
    plot_training_history()
    plot_actual_vs_predicted()
    plot_per_node_metrics()
    plot_per_horizon_metrics()
    plot_model_comparison()
    plot_prediction_examples()
    plot_error_distribution()
    print("\nAll visualizations saved to results/plots/")