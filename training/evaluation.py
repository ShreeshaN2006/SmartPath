"""
Evaluation Metrics for Traffic Forecasting
------------------------------------------
"""

import torch
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, List, Tuple


def safe_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-8) -> float:
    """MAPE with protection against division by zero."""
    mask = np.abs(y_true) > epsilon
    if not mask.any():
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute all metrics for a single prediction.

    Args:
        y_true: (n_samples, horizon, n_nodes) or (n_samples, n_nodes)
        y_pred: Same shape as y_true

    Returns:
        Dict with MAE, RMSE, MAPE, R2
    """
    # Flatten for overall metrics
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()

    mae = mean_absolute_error(y_true_flat, y_pred_flat)
    rmse = np.sqrt(mean_squared_error(y_true_flat, y_pred_flat))
    mape = safe_mape(y_true_flat, y_pred_flat)
    r2 = r2_score(y_true_flat, y_pred_flat)

    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
        'R2': r2
    }


def compute_per_node_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                              node_names: List[str]) -> pd.DataFrame:
    """
    Compute metrics per node.

    Args:
        y_true: (n_samples, horizon, n_nodes)
        y_pred: (n_samples, horizon, n_nodes)
        node_names: List of node names

    Returns:
        DataFrame with per-node metrics
    """
    n_samples, horizon, n_nodes = y_true.shape
    results = []

    for i in range(n_nodes):
        node_true = y_true[:, :, i].flatten()
        node_pred = y_pred[:, :, i].flatten()

        mae = mean_absolute_error(node_true, node_pred)
        rmse = np.sqrt(mean_squared_error(node_true, node_pred))
        mape = safe_mape(node_true, node_pred)
        r2 = r2_score(node_true, node_pred)

        results.append({
            'node_id': i,
            'node_name': node_names[i],
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R2': r2
        })

    return pd.DataFrame(results)


def compute_per_horizon_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    """
    Compute metrics per prediction horizon step.

    Args:
        y_true: (n_samples, horizon, n_nodes)
        y_pred: (n_samples, horizon, n_nodes)

    Returns:
        DataFrame with per-horizon metrics
    """
    n_samples, horizon, n_nodes = y_true.shape
    results = []

    for h in range(horizon):
        h_true = y_true[:, h, :].flatten()
        h_pred = y_pred[:, h, :].flatten()

        mae = mean_absolute_error(h_true, h_pred)
        rmse = np.sqrt(mean_squared_error(h_true, h_pred))
        mape = safe_mape(h_true, h_pred)
        r2 = r2_score(h_true, h_pred)

        results.append({
            'horizon': h + 1,
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R2': r2
        })

    return pd.DataFrame(results)


def evaluate_model(model, dataloader, device: torch.device,
                   target_scaler, node_names: List[str]) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    """
    Evaluate model on a dataloader.

    Returns:
        overall_metrics, per_node_df, per_horizon_df
    """
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for x, y in dataloader:
            x = x.to(device)
            y = y.to(device)

            out = model(x)  # (batch, horizon, nodes, 1)
            out = out.squeeze(-1)  # (batch, horizon, nodes)

            all_preds.append(out.cpu().numpy())
            all_targets.append(y.cpu().numpy())

    y_pred = np.concatenate(all_preds, axis=0)
    y_true = np.concatenate(all_targets, axis=0)

    # Inverse transform
    y_pred_orig = target_scaler.inverse_transform(y_pred.reshape(-1, 1)).reshape(y_pred.shape)
    y_true_orig = target_scaler.inverse_transform(y_true.reshape(-1, 1)).reshape(y_true.shape)

    # Compute metrics
    overall = compute_metrics(y_true_orig, y_pred_orig)
    per_node = compute_per_node_metrics(y_true_orig, y_pred_orig, node_names)
    per_horizon = compute_per_horizon_metrics(y_true_orig, y_pred_orig)

    return overall, per_node, per_horizon


if __name__ == "__main__":
    # Test metrics
    y_true = np.random.rand(100, 1, 16) * 50
    y_pred = y_true + np.random.randn(100, 1, 16) * 5

    overall = compute_metrics(y_true, y_pred)
    print("Overall metrics:", overall)

    node_names = [f"Node_{i}" for i in range(16)]
    per_node = compute_per_node_metrics(y_true, y_pred, node_names)
    print(per_node.head())

    per_horizon = compute_per_horizon_metrics(y_true, y_pred)
    print(per_horizon)