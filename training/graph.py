"""
Graph Construction for DCRNN
----------------------------
Constructs adjacency matrix for the 16 traffic nodes.

Since GPS coordinates are not provided in the original dataset,
this creates a provisional adjacency matrix based on:
1. Area proximity (nodes in same area are connected)
2. Known major road connections in Bangalore

The adjacency matrix is saved and can be replaced with a real
road-network adjacency matrix when coordinates become available.

Node IDs (from traffic_nodes.csv):
0: Hosur Road (Electronic City)
1: Silk Board Junction (Electronic City)
2: Ballari Road (Hebbal)
3: Hebbal Flyover (Hebbal)
4: 100 Feet Road (Indiranagar)
5: CMH Road (Indiranagar)
6: Jayanagar 4th Block (Jayanagar)
7: South End Circle (Jayanagar)
8: Sarjapur Road (Koramangala)
9: Sony World Junction (Koramangala)
10: Anil Kumble Circle (M.G. Road)
11: Trinity Circle (M.G. Road)
12: ITPL Main Road (Whitefield)
13: Marathahalli Bridge (Whitefield)
14: Tumkur Road (Yeshwanthpur)
15: Yeshwanthpur Circle (Yeshwanthpur)
"""

import numpy as np
import pandas as pd
from pathlib import Path


def create_provisional_adjacency() -> np.ndarray:
    """
    Create a provisional 16x16 adjacency matrix.

    Connections based on:
    - Same area = strong connection (weight 1.0)
    - Known major road corridors = medium connection (weight 0.5)
    - Self-loops = 1.0

    This is PROVISIONAL and should be replaced with real
    road-network adjacency when coordinates are available.
    """
    n_nodes = 16
    adj = np.zeros((n_nodes, n_nodes))

    # Self-loops
    np.fill_diagonal(adj, 1.0)

    # Area-based connections (strong: weight 1.0)
    area_groups = {
        'Electronic City': [0, 1],      # Hosur Road, Silk Board
        'Hebbal': [2, 3],                # Ballari Road, Hebbal Flyover
        'Indiranagar': [4, 5],           # 100 Feet Road, CMH Road
        'Jayanagar': [6, 7],             # Jayanagar 4th Block, South End Circle
        'Koramangala': [8, 9],           # Sarjapur Road, Sony World Junction
        'M.G. Road': [10, 11],           # Anil Kumble Circle, Trinity Circle
        'Whitefield': [12, 13],          # ITPL Main Road, Marathahalli Bridge
        'Yeshwanthpur': [14, 15],        # Tumkur Road, Yeshwanthpur Circle
    }

    for area, nodes in area_groups.items():
        for i in nodes:
            for j in nodes:
                if i != j:
                    adj[i, j] = 1.0
                    adj[j, i] = 1.0

    # Known corridor connections (medium: weight 0.5)
    # These represent major arterial roads connecting areas
    corridor_connections = [
        # Outer Ring Road corridor
        (1, 9),   # Silk Board -> Sony World (ORR)
        (9, 13),  # Sony World -> Marathahalli (ORR)
        (13, 12), # Marathahalli -> ITPL (Whitefield)
        # Inner corridors
        (10, 11), # M.G. Road circles
        (10, 4),  # M.G. Road -> Indiranagar
        (11, 5),  # Trinity -> CMH Road
        (4, 8),   # 100 Feet -> Sarjapur (via Koramangala)
        (5, 8),   # CMH -> Sarjapur
        (6, 7),   # Jayanagar internal
        (14, 15), # Yeshwanthpur internal
        (2, 3),   # Hebbal internal
        # Cross-city
        (1, 8),   # Silk Board -> Sarjapur (major junction)
        (9, 8),   # Sony World -> Sarjapur
    ]

    for i, j in corridor_connections:
        adj[i, j] = max(adj[i, j], 0.5)
        adj[j, i] = max(adj[j, i], 0.5)

    # Normalize rows (row-stochastic for diffusion convolution)
    row_sums = adj.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    adj_normalized = adj / row_sums

    return adj_normalized


def load_adjacency_matrix(path: str = None) -> np.ndarray:
    """
    Load adjacency matrix from CSV or create provisional one.
    """
    if path and Path(path).exists():
        df = pd.read_csv(path, index_col=0)
        return df.values
    return create_provisional_adjacency()


def save_adjacency_matrix(adj: np.ndarray, path: str):
    """Save adjacency matrix to CSV with node labels."""
    nodes_df = pd.read_csv('data/traffic/traffic_nodes.csv')
    node_names = nodes_df['Road/Intersection Name'].tolist()
    df = pd.DataFrame(adj, index=node_names, columns=node_names)
    df.to_csv(path)
    print(f"Saved adjacency matrix to {path}")
    print(f"Shape: {adj.shape}")
    print(f"Row sums: {adj.sum(axis=1)}")


def compute_chebyshev_polynomials(adj: np.ndarray, K: int) -> list:
    """
    Compute Chebyshev polynomials up to order K for diffusion convolution.
    T_0 = I, T_1 = L, T_k = 2 * L * T_{k-1} - T_{k-2}
    where L is the scaled Laplacian.
    """
    n = adj.shape[0]
    # Graph Laplacian: L = I - D^{-1/2} A D^{-1/2}
    # For row-normalized adj, we use L = I - A
    L = np.eye(n) - adj

    # Scale Laplacian to [-1, 1]
    lambda_max = 2.0  # approximate for normalized Laplacian
    L_scaled = (2.0 / lambda_max) * L - np.eye(n)

    T = [np.eye(n), L_scaled.copy()]
    for k in range(2, K):
        T_k = 2 * L_scaled @ T[k-1] - T[k-2]
        T.append(T_k)

    return T


if __name__ == "__main__":
    # Create and save provisional adjacency matrix
    adj = create_provisional_adjacency()
    save_adjacency_matrix(adj, 'data/traffic/adjacency_matrix.csv')

    # Also save raw (non-normalized) for reference
    adj_raw = create_provisional_adjacency()
    # Remove normalization for raw version
    nodes_df = pd.read_csv('data/traffic/traffic_nodes.csv')
    node_names = nodes_df['Road/Intersection Name'].tolist()

    # Create raw version with same logic but no normalization
    n_nodes = 16
    adj_raw = np.zeros((n_nodes, n_nodes))
    np.fill_diagonal(adj_raw, 1.0)

    area_groups = {
        'Electronic City': [0, 1], 'Hebbal': [2, 3], 'Indiranagar': [4, 5],
        'Jayanagar': [6, 7], 'Koramangala': [8, 9], 'M.G. Road': [10, 11],
        'Whitefield': [12, 13], 'Yeshwanthpur': [14, 15],
    }

    for area, nodes in area_groups.items():
        for i in nodes:
            for j in nodes:
                if i != j:
                    adj_raw[i, j] = 1.0
                    adj_raw[j, i] = 1.0

    corridor_connections = [
        (1, 9), (9, 13), (13, 12), (10, 11), (10, 4), (11, 5),
        (4, 8), (5, 8), (6, 7), (14, 15), (2, 3), (1, 8), (9, 8),
    ]
    for i, j in corridor_connections:
        adj_raw[i, j] = max(adj_raw[i, j], 0.5)
        adj_raw[j, i] = max(adj_raw[j, i], 0.5)

    df_raw = pd.DataFrame(adj_raw, index=node_names, columns=node_names)
    df_raw.to_csv('data/traffic/adjacency_matrix_raw.csv')
    print("Saved raw adjacency matrix to data/traffic/adjacency_matrix_raw.csv")