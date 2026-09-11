"""
Baseline Models for Traffic Forecasting
----------------------------------------
Implements:
1. Historical Mean
2. Naive Previous-Day
3. Linear Regression / Ridge
4. Random Forest
5. XGBoost
6. LSTM (PyTorch)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
import xgboost as xgb
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from typing import Dict, Tuple, List
import joblib
from pathlib import Path
from tqdm import tqdm


# ─── Baseline 1: Historical Mean ───
class HistoricalMeanBaseline:
    """Predict using historical mean per node."""

    def __init__(self):
        self.means = None

    def fit(self, y_train: np.ndarray):
        """y_train: (n_samples, horizon, n_nodes)"""
        self.means = y_train.mean(axis=(0, 1))  # (n_nodes,)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """X: (n_samples, seq_len, n_nodes, n_features)"""
        n_samples = X.shape[0]
        horizon = 1  # Assume horizon=1 for simplicity
        return np.tile(self.means, (n_samples, horizon, 1))


# ─── Baseline 2: Naive Previous-Day ───
class NaivePreviousDayBaseline:
    """Predict using last observed value."""

    def fit(self, y_train: np.ndarray):
        pass  # No training needed

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Use last timestep's Average Speed (first feature) as prediction."""
        # X: (n_samples, seq_len, n_nodes, n_features)
        # Average Speed is feature index 1
        last_speed = X[:, -1, :, 1:2]  # (n_samples, n_nodes, 1)
        return last_speed.transpose(0, 2, 1)  # (n_samples, 1, n_nodes)


# ─── Baseline 3: Ridge Regression ───
class RidgeBaseline:
    """Ridge regression with multi-output."""

    def __init__(self, alpha: float = 1.0):
        self.model = MultiOutputRegressor(Ridge(alpha=alpha, random_state=42))
        self.feature_scaler = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        """Flatten spatial-temporal to tabular."""
        n_samples, seq_len, n_nodes, n_features = X_train.shape
        horizon = y_train.shape[1]

        # Reshape: (n_samples * n_nodes, seq_len * n_features)
        X_flat = X_train.reshape(n_samples, -1)
        # y: (n_samples * n_nodes, horizon)
        y_flat = y_train.reshape(n_samples, -1)

        self.model.fit(X_flat, y_flat)

    def predict(self, X: np.ndarray) -> np.ndarray:
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)
        y_pred = self.model.predict(X_flat)
        horizon = y_pred.shape[1] // X.shape[2]
        return y_pred.reshape(n_samples, horizon, -1)


# ─── Baseline 4: Random Forest ───
class RandomForestBaseline:
    """Random Forest with multi-output."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 10):
        self.model = MultiOutputRegressor(
            RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth,
                                  random_state=42, n_jobs=-1)
        )

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        n_samples, seq_len, n_nodes, n_features = X_train.shape
        X_flat = X_train.reshape(n_samples, -1)
        y_flat = y_train.reshape(n_samples, -1)
        self.model.fit(X_flat, y_flat)

    def predict(self, X: np.ndarray) -> np.ndarray:
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)
        y_pred = self.model.predict(X_flat)
        horizon = y_pred.shape[1] // X.shape[2]
        return y_pred.reshape(n_samples, horizon, -1)


# ─── Baseline 5: XGBoost ───
class XGBoostBaseline:
    """XGBoost with multi-output."""

    def __init__(self, n_estimators: int = 200, max_depth: int = 6, learning_rate: float = 0.1):
        self.models = []
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.horizon = None
        self.n_nodes = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        n_samples, seq_len, n_nodes, n_features = X_train.shape
        self.horizon = y_train.shape[1]
        self.n_nodes = n_nodes

        X_flat = X_train.reshape(n_samples, -1)
        y_flat = y_train.reshape(n_samples, -1)  # (n_samples, horizon * n_nodes)

        self.models = []
        for i in range(y_flat.shape[1]):
            model = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )
            model.fit(X_flat, y_flat[:, i])
            self.models.append(model)

    def predict(self, X: np.ndarray) -> np.ndarray:
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)

        preds = []
        for model in self.models:
            preds.append(model.predict(X_flat))

        y_pred = np.column_stack(preds)
        return y_pred.reshape(n_samples, self.horizon, self.n_nodes)


# ─── Baseline 6: LSTM ───
class LSTMModel(nn.Module):
    """Simple LSTM for traffic forecasting (no graph)."""

    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2,
                 output_dim: int = 1, horizon: int = 1, dropout: float = 0.2):
        super().__init__()
        self.horizon = horizon
        self.output_dim = output_dim

        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim * horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, seq_len, nodes, features) -> reshape to (batch * nodes, seq_len, features)
        """
        batch, seq_len, nodes, features = x.shape
        x = x.reshape(batch * nodes, seq_len, features)

        out, _ = self.lstm(x)  # (batch * nodes, seq_len, hidden)
        out = out[:, -1]  # (batch * nodes, hidden)
        out = self.fc(out)  # (batch * nodes, horizon)
        out = out.reshape(batch, nodes, self.horizon)
        return out.transpose(1, 2)  # (batch, horizon, nodes)


class LSTMBaseline:
    """LSTM baseline wrapper."""

    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2,
                 horizon: int = 1, lr: float = 0.001, epochs: int = 50,
                 batch_size: int = 32, device: str = 'cpu'):
        self.model = LSTMModel(input_dim, hidden_dim, num_layers, 1, horizon).to(device)
        self.device = device
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.input_dim = input_dim
        self.horizon = horizon

    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: np.ndarray = None, y_val: np.ndarray = None):
        train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        val_loader = None
        if X_val is not None:
            val_dataset = TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val))
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        for epoch in range(self.epochs):
            self.model.train()
            train_loss = 0
            for x, y in tqdm(train_loader, desc=f"Epoch {epoch+1}/{self.epochs}", leave=False):
                x, y = x.to(self.device), y.to(self.device)
                optimizer.zero_grad()
                out = self.model(x)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            if val_loader:
                self.model.eval()
                val_loss = 0
                with torch.no_grad():
                    for x, y in val_loader:
                        x, y = x.to(self.device), y.to(self.device)
                        out = self.model(x)
                        val_loss += criterion(out, y).item()
                val_loss /= len(val_loader)
                print(f"Epoch {epoch+1}: Train Loss={train_loss/len(train_loader):.4f}, Val Loss={val_loss:.4f}")
            else:
                print(f"Epoch {epoch+1}: Train Loss={train_loss/len(train_loader):.4f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(X).to(self.device)
            out = self.model(x)
        return out.cpu().numpy()


# ─── Evaluation Helper ───
def evaluate_baseline(name: str, model, X_test: np.ndarray, y_test: np.ndarray,
                      target_scaler, node_names: List[str],
                      device: str = 'cpu') -> Dict:
    """Evaluate a baseline model."""
    from training.evaluation import compute_metrics, compute_per_node_metrics, compute_per_horizon_metrics

    # Predict
    if hasattr(model, 'predict'):
        y_pred = model.predict(X_test)
    else:
        # PyTorch model
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


def run_all_baselines(X_train, y_train, X_val, y_val, X_test, y_test,
                      target_scaler, node_names: List[str],
                      device: str = 'cpu') -> List[Dict]:
    """Run all baseline models and return results."""
    results = []

    print("\n" + "="*60)
    print("BASELINE 1: Historical Mean")
    print("="*60)
    hm = HistoricalMeanBaseline()
    hm.fit(y_train)
    results.append(evaluate_baseline('HistoricalMean', hm, X_test, y_test, target_scaler, node_names))

    print("\n" + "="*60)
    print("BASELINE 2: Naive Previous-Day")
    print("="*60)
    npd = NaivePreviousDayBaseline()
    npd.fit(y_train)
    results.append(evaluate_baseline('NaivePreviousDay', npd, X_test, y_test, target_scaler, node_names))

    print("\n" + "="*60)
    print("BASELINE 3: Ridge Regression")
    print("="*60)
    ridge = RidgeBaseline(alpha=1.0)
    ridge.fit(X_train, y_train)
    results.append(evaluate_baseline('Ridge', ridge, X_test, y_test, target_scaler, node_names))

    print("\n" + "="*60)
    print("BASELINE 4: Random Forest")
    print("="*60)
    rf = RandomForestBaseline(n_estimators=100, max_depth=10)
    rf.fit(X_train, y_train)
    results.append(evaluate_baseline('RandomForest', rf, X_test, y_test, target_scaler, node_names))

    print("\n" + "="*60)
    print("BASELINE 5: XGBoost")
    print("="*60)
    xgb_model = XGBoostBaseline(n_estimators=200, max_depth=6, learning_rate=0.1)
    xgb_model.fit(X_train, y_train)
    results.append(evaluate_baseline('XGBoost', xgb_model, X_test, y_test, target_scaler, node_names))

    print("\n" + "="*60)
    print("BASELINE 6: LSTM")
    print("="*60)
    lstm = LSTMBaseline(input_dim=X_train.shape[-1], hidden_dim=64, num_layers=2,
                        horizon=y_train.shape[1], lr=0.001, epochs=30,
                        batch_size=32, device=device)
    lstm.fit(X_train, y_train, X_val, y_val)
    results.append(evaluate_baseline('LSTM', lstm, X_test, y_test, target_scaler, node_names, device))

    return results


if __name__ == "__main__":
    from training.preprocessing import prepare_data

    X_train, y_train, X_val, y_val, X_test, y_test, _, target_scaler, _, node_names, _ = \
        prepare_data('data/traffic/smartpath_traffic_model_ready.csv', seq_len=7, horizon=1)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    results = run_all_baselines(X_train, y_train, X_val, y_val, X_test, y_test,
                                target_scaler, node_names, device)

    # Save results
    Path('results').mkdir(exist_ok=True)
    for r in results:
        r['per_node'].to_csv(f'results/baseline_{r["name"]}_per_node.csv', index=False)
        r['per_horizon'].to_csv(f'results/baseline_{r["name"]}_per_horizon.csv', index=False)

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