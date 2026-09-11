"""
PyTorch Dataset and DataLoader for DCRNN
-----------------------------------------
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple


class TrafficDataset(Dataset):
    """Dataset for graph time-series traffic data."""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        Args:
            X: (n_samples, seq_len, n_nodes, n_features)
            y: (n_samples, horizon, n_nodes)
        """
        self.X = torch.from_numpy(X).float()
        self.y = torch.from_numpy(y).float()

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def create_dataloaders(X_train, y_train, X_val, y_val, X_test, y_test,
                       batch_size: int = 32, num_workers: int = 0):
    """Create train, val, test dataloaders."""
    train_dataset = TrafficDataset(X_train, y_train)
    val_dataset = TrafficDataset(X_val, y_val)
    test_dataset = TrafficDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size,
                              shuffle=True, num_workers=num_workers, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size,
                            shuffle=False, num_workers=num_workers, drop_last=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size,
                             shuffle=False, num_workers=num_workers, drop_last=False)

    return train_loader, val_loader, test_loader


if __name__ == "__main__":
    from training.preprocessing import prepare_data

    X_train, y_train, X_val, y_val, X_test, y_test, _, _, _, _, _ = \
        prepare_data('data/traffic/smartpath_traffic_model_ready.csv', seq_len=7, horizon=1)

    train_loader, val_loader, test_loader = create_dataloaders(
        X_train, y_train, X_val, y_val, X_test, y_test, batch_size=32
    )

    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")

    # Test batch
    x, y = next(iter(train_loader))
    print(f"Batch X shape: {x.shape}")
    print(f"Batch y shape: {y.shape}")