"""
Data Preprocessing for DCRNN
----------------------------
Handles:
- Loading and validating the traffic dataset
- Creating complete date range with forward-fill per node
- Chronological train/val/test split
- Feature selection and engineering
- Normalization (fit on train only)
- Sequence generation for graph time-series
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')


# ─── Feature Configuration ───
TARGET_COL = 'Average Speed'

FEATURE_COLS = [
    'Traffic Volume',
    'Average Speed',
    'Travel Time Index',
    'Congestion Level',
    'Road Capacity Utilization',
    'Incident Reports',
    'Environmental Impact',
    'Public Transport Usage',
    'Traffic Signal Compliance',
    'Parking Usage',
    'Pedestrian and Cyclist Count',
    'day_of_week',
    'month',
    'is_weekend',
    'weather_code',
    'roadwork_code',
    'speed_lag_1d',
    'volume_lag_1d',
    'congestion_lag_1d',
    'speed_rolling_3d',
    'speed_rolling_7d',
]

CATEGORICAL_COLS = ['Weather Conditions', 'Roadwork and Construction Activity']

DROP_COLS = [
    'Travel Time Index',
    'Road Capacity Utilization',
    'speed_lag_2d', 'volume_lag_2d', 'congestion_lag_2d',
    'speed_lag_3d', 'volume_lag_3d', 'congestion_lag_3d',
    'speed_lag_7d', 'volume_lag_7d', 'congestion_lag_7d',
    'quarter',
]


def load_and_validate_data(csv_path: str) -> pd.DataFrame:
    """Load CSV and perform validation checks."""
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])

    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Unique nodes: {df['Road/Intersection Name'].nunique()}")
    print(f"Missing values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")

    # Check for duplicates
    dup = df.duplicated(subset=['Date', 'Road/Intersection Name']).sum()
    print(f"Duplicate (Date, Road) pairs: {dup}")

    return df


def encode_categorical(df: pd.DataFrame, fit_encoders: dict = None) -> tuple:
    """Encode categorical variables. Returns (df, encoders)."""
    from sklearn.preprocessing import LabelEncoder

    df = df.copy()
    encoders = {}

    for col in CATEGORICAL_COLS:
        if col in df.columns:
            if fit_encoders and col in fit_encoders:
                le = fit_encoders[col]
                df[col] = df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            else:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                encoders[col] = le

    return df, encoders


def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """Select and prepare features for modeling."""
    df = df.copy()

    # Drop redundant columns
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns], errors='ignore')

    # Fill NaN in lag/rolling features with 0
    lag_cols = [c for c in df.columns if 'lag_' in c or 'rolling_' in c]
    for col in lag_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Encode categoricals
    df, encoders = encode_categorical(df)

    # Ensure all feature columns exist
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    missing = set(FEATURE_COLS) - set(available_features)
    if missing:
        print(f"Warning: Missing features: {missing}")

    return df, available_features, encoders


def create_complete_dataset(df: pd.DataFrame, feature_cols: list, target_col: str,
                           node_names: list) -> tuple:
    """
    Create complete synchronized dataset with continuous date range.
    Forward-fills missing values per node.
    """
    # Create complete date range from min to max date in the data
    date_min = df['Date'].min()
    date_max = df['Date'].max()
    complete_dates = pd.date_range(start=date_min, end=date_max, freq='D')
    print(f"Complete date range: {date_min} to {date_max} ({len(complete_dates)} days)")

    # Pivot to (date, node) matrix for each feature, reindex to complete date range
    feature_data = {}
    for col in feature_cols:
        pivot = df.pivot(index='Date', columns='Road/Intersection Name', values=col)
        pivot = pivot.reindex(columns=node_names)
        # Reindex to complete date range and forward fill missing values per node
        pivot = pivot.reindex(complete_dates).ffill().bfill()
        feature_data[col] = pivot.values  # (n_dates, n_nodes)

    target_pivot = df.pivot(index='Date', columns='Road/Intersection Name', values=target_col)
    target_pivot = target_pivot.reindex(columns=node_names)
    target_pivot = target_pivot.reindex(complete_dates).ffill().bfill()
    target_data = target_pivot.values  # (n_dates, n_nodes)

    n_dates, n_nodes = target_data.shape
    n_features = len(feature_cols)

    # Stack features: (n_dates, n_nodes, n_features)
    X_all = np.stack([feature_data[col] for col in feature_cols], axis=-1)

    # Check for any remaining NaN
    if np.isnan(X_all).any():
        print("Warning: NaN in features after filling, replacing with 0")
        X_all = np.nan_to_num(X_all, nan=0.0)
    if np.isnan(target_data).any():
        print("Warning: NaN in target after filling, replacing with 0")
        target_data = np.nan_to_num(target_data, nan=0.0)

    return X_all, target_data, complete_dates


def split_data_chronological(X_all: np.ndarray, target_data: np.ndarray,
                             dates: pd.DatetimeIndex,
                             train_ratio=0.7, val_ratio=0.15):
    """Split data chronologically by date index."""
    n_dates = len(dates)
    train_end = int(n_dates * train_ratio)
    val_end = int(n_dates * (train_ratio + val_ratio))

    train_dates = dates[:train_end]
    val_dates = dates[train_end:val_end]
    test_dates = dates[val_end:]

    X_train = X_all[:train_end]
    X_val = X_all[train_end:val_end]
    X_test = X_all[val_end:]

    y_train = target_data[:train_end]
    y_val = target_data[train_end:val_end]
    y_test = target_data[val_end:]

    print(f"Train dates: {train_dates[0]} to {train_dates[-1]} ({len(X_train)} days)")
    print(f"Val dates:   {val_dates[0]} to {val_dates[-1]} ({len(X_val)} days)")
    print(f"Test dates:  {test_dates[0]} to {test_dates[-1]} ({len(X_test)} days)")

    return (X_train, y_train, X_val, y_val, X_test, y_test,
            (train_dates, val_dates, test_dates))


def create_sequences(X: np.ndarray, y: np.ndarray,
                     seq_len: int, horizon: int) -> tuple:
    """
    Generate sequences from continuous data.

    Args:
        X: (n_dates, n_nodes, n_features)
        y: (n_dates, n_nodes)
        seq_len: Input sequence length
        horizon: Prediction horizon

    Returns:
        X_seq: (n_samples, seq_len, n_nodes, n_features)
        y_seq: (n_samples, horizon, n_nodes)
    """
    n_dates, n_nodes, n_features = X.shape

    X_seq, y_seq = [], []
    for i in range(n_dates - seq_len - horizon + 1):
        X_seq.append(X[i:i+seq_len])      # (seq_len, n_nodes, n_features)
        y_seq.append(y[i+seq_len:i+seq_len+horizon])  # (horizon, n_nodes)

    if not X_seq:
        raise ValueError(f"Not enough data for seq_len={seq_len}, horizon={horizon}")

    X_seq = np.array(X_seq)  # (n_samples, seq_len, n_nodes, n_features)
    y_seq = np.array(y_seq)  # (n_samples, horizon, n_nodes)

    print(f"Generated {len(X_seq)} sequences")
    print(f"X shape: {X_seq.shape}")
    print(f"y shape: {y_seq.shape}")

    return X_seq, y_seq


def fit_scalers(X_train: np.ndarray, y_train: np.ndarray, feature_cols: list, target_col: str):
    """Fit scalers on training data only."""
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()

    n_train, n_nodes, n_features = X_train.shape
    X_train_flat = X_train.reshape(-1, n_features)
    feature_scaler.fit(X_train_flat)

    y_train_flat = y_train.reshape(-1, 1)
    target_scaler.fit(y_train_flat)

    return feature_scaler, target_scaler


def apply_scalers(X: np.ndarray, y: np.ndarray,
                  feature_scaler: StandardScaler, target_scaler: StandardScaler):
    """Apply fitted scalers to data."""
    n_dates, n_nodes, n_features = X.shape
    X_flat = X.reshape(-1, n_features)
    X_scaled = feature_scaler.transform(X_flat).reshape(n_dates, n_nodes, n_features)

    y_flat = y.reshape(-1, 1)
    y_scaled = target_scaler.transform(y_flat).reshape(n_dates, n_nodes)

    return X_scaled, y_scaled


def prepare_data(csv_path: str, seq_len: int = 7, horizon: int = 1,
                 train_ratio=0.7, val_ratio=0.15):
    """
    Full preprocessing pipeline.

    Returns:
        X_train, y_train, X_val, y_val, X_test, y_test
        feature_scaler, target_scaler
        feature_cols, node_names
        date_splits
    """
    # Load and validate
    df = load_and_validate_data(csv_path)

    # Get node names in consistent order
    nodes_df = pd.read_csv('data/traffic/traffic_nodes.csv')
    node_names = nodes_df['Road/Intersection Name'].tolist()

    # Select features
    df, feature_cols, encoders = select_features(df)

    # Create complete synchronized dataset
    X_all, target_data, complete_dates = create_complete_dataset(
        df, feature_cols, TARGET_COL, node_names
    )

    # Chronological split
    (X_train, y_train, X_val, y_val, X_test, y_test,
     date_splits) = split_data_chronological(
        X_all, target_data, complete_dates, train_ratio, val_ratio
    )

    # Fit scalers on train
    feature_scaler, target_scaler = fit_scalers(X_train, y_train, feature_cols, TARGET_COL)

    # Apply scalers
    X_train, y_train = apply_scalers(X_train, y_train, feature_scaler, target_scaler)
    X_val, y_val = apply_scalers(X_val, y_val, feature_scaler, target_scaler)
    X_test, y_test = apply_scalers(X_test, y_test, feature_scaler, target_scaler)

    # Create sequences
    X_train_seq, y_train_seq = create_sequences(X_train, y_train, seq_len, horizon)
    X_val_seq, y_val_seq = create_sequences(X_val, y_val, seq_len, horizon)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, seq_len, horizon)

    # Save scalers
    Path('models/scalers').mkdir(parents=True, exist_ok=True)
    joblib.dump(feature_scaler, 'models/scalers/feature_scaler.pkl')
    joblib.dump(target_scaler, 'models/scalers/target_scaler.pkl')
    joblib.dump(encoders, 'models/scalers/categorical_encoders.pkl')
    joblib.dump(feature_cols, 'models/scalers/feature_cols.pkl')
    joblib.dump(node_names, 'models/scalers/node_names.pkl')

    return (X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_seq, y_test_seq,
            feature_scaler, target_scaler,
            feature_cols, node_names,
            date_splits)


if __name__ == "__main__":
    prepare_data('data/traffic/smartpath_traffic_model_ready.csv', seq_len=7, horizon=1)