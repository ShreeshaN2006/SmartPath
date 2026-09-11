"""
Run Baseline Models for Comparison
-----------------------------------
Runs fast baselines and optionally slower ones.
"""

import numpy as np
import pandas as pd
import torch
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from typing import Dict, List
import joblib

from training.preprocessing import prepare_data
from training.baselines import (HistoricalMeanBaseline, NaivePreviousDayBaseline,
                                RidgeBaseline, RandomForestBaseline, XGBoostBaseline)
from training.evaluation import compute_metrics, compute_per_node_metrics, compute_per_horizon_metrics


def evaluate_baseline(name: str, model, X_test: np.ndarray, y_test: np.ndarray,
                      target_scaler, node_names: List[str]) -> Dict:
    """Evaluate a baseline model."""
    # Predict
    if hasattr(model, 'predict'):
        y_pred = model.predict(X_test)
    else:
        # PyTorch model
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(X_test).to(device)
            y_pred = model(x).cpu().numpy()

    # Inverse transform
    y_pred_orig = target_scaler.inverse_transform(y_pred.reshape(-1, 1)).reshape(y_pred.shape)
    y_true_orig = target_scaler.inverse_transform(y_test.reshape(-1, 1)).reshape(y_test.shape)

    # Metrics
    overall = compute_metrics(y_true_orig, y_pred_orig)
    per_node = compute_per_node_metrics(y_true_orig, y_pred_orig, node_names)
    per_horizon = compute_per_horizon_metrics(y_true_orig, y_pred_orig)

    return {
        'name': name,
        'overall': overall,
        'per_node': per_node,
        'per_horizon': per_horizon,
        'predictions': y_pred_orig
    }


def main():
    print("Loading data...")
    X_train, y_train, X_val, y_val, X_test, y_test, _, target_scaler, _, node_names, _ = \
        prepare_data('data/traffic/smartpath_traffic_model_ready.csv', seq_len=7, horizon=1)

    Path('results').mkdir(exist_ok=True)
    results = []

    # 1. Historical Mean
    print("\n" + "="*60)
    print("BASELINE 1: Historical Mean")
    print("="*60)
    hm = HistoricalMeanBaseline()
    hm.fit(y_train)
    results.append(evaluate_baseline('HistoricalMean', hm, X_test, y_test, target_scaler, node_names))

    # 2. Naive Previous-Day
    print("\n" + "="*60)
    print("BASELINE 2: Naive Previous-Day")
    print("="*60)
    npd = NaivePreviousDayBaseline()
    npd.fit(y_train)
    results.append(evaluate_baseline('NaivePreviousDay', npd, X_test, y_test, target_scaler, node_names))

    # 3. Ridge Regression
    print("\n" + "="*60)
    print("BASELINE 3: Ridge Regression")
    print("="*60)
    ridge = RidgeBaseline(alpha=1.0)
    ridge.fit(X_train, y_train)
    results.append(evaluate_baseline('Ridge', ridge, X_test, y_test, target_scaler, node_names))

    # 4. Random Forest (reduced params for speed)
    print("\n" + "="*60)
    print("BASELINE 4: Random Forest")
    print("="*60)
    rf = RandomForestBaseline(n_estimators=50, max_depth=8)
    rf.fit(X_train, y_train)
    results.append(evaluate_baseline('RandomForest', rf, X_test, y_test, target_scaler, node_names))

    # 5. XGBoost (reduced params for speed)
    print("\n" + "="*60)
    print("BASELINE 5: XGBoost")
    print("="*60)
    xgb_model = XGBoostBaseline(n_estimators=100, max_depth=5, learning_rate=0.1)
    xgb_model.fit(X_train, y_train)
    results.append(evaluate_baseline('XGBoost', xgb_model, X_test, y_test, target_scaler, node_names))

    # Save results
    for r in results:
        r['per_node'].to_csv(f'results/baseline_{r["name"]}_per_node.csv', index=False)
        r['per_horizon'].to_csv(f'results/baseline_{r["name"]}_per_horizon.csv', index=False)
        np.savez(f'results/baseline_{r["name"]}_predictions.npz',
                 y_pred=r['predictions'], y_true=target_scaler.inverse_transform(
                     y_test.reshape(-1, 1)).reshape(y_test.shape))

    # Summary
    summary = pd.DataFrame([{
        'Model': r['name'],
        'MAE': r['overall']['MAE'],
        'RMSE': r['overall']['RMSE'],
        'MAPE': r['overall']['MAPE'],
        'R2': r['overall']['R2']
    } for r in results])
    summary.to_csv('results/baseline_results.csv', index=False)
    print("\nBaseline Summary:")
    print(summary)

    # Also add DCRNN results for comparison
    dcrnn_results = pd.read_csv('results/dcrnn_results.csv')
    print("\nDCRNN Results:")
    print(dcrnn_results[['MAE', 'RMSE', 'MAPE', 'R2']])

    combined = pd.concat([summary, dcrnn_results[['MAE', 'RMSE', 'MAPE', 'R2']].assign(Model='DCRNN')], ignore_index=True)
    combined.to_csv('results/model_comparison.csv', index=False)
    print("\nModel Comparison:")
    print(combined)


if __name__ == '__main__':
    main()