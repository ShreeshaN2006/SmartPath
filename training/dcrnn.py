"""
DCRNN Model Implementation
--------------------------
Diffusion Convolutional Recurrent Neural Network for traffic forecasting.

Based on: "Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting"
by Li et al. (ICLR 2018)

Architecture:
- Encoder: Stack of DCGRU layers
- Decoder: Stack of DCGRU layers with teacher forcing
- Output: Linear projection to prediction horizon
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple
import numpy as np


class DiffusionGraphConv(nn.Module):
    """
    Diffusion Graph Convolution Layer.

    Computes: sum_{k=0}^{K-1} (T_k(L) * X) * W_k
    where T_k are Chebyshev polynomials of the scaled Laplacian.
    """

    def __init__(self, in_channels: int, out_channels: int, K: int = 2):
        super().__init__()
        self.K = K
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Weight for each Chebyshev polynomial order
        self.weights = nn.Parameter(torch.FloatTensor(K, in_channels, out_channels))
        self.bias = nn.Parameter(torch.FloatTensor(out_channels))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.weights)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor, cheb_polys: List[torch.Tensor]) -> torch.Tensor:
        """
        Args:
            x: (batch, nodes, in_channels)
            cheb_polys: List of K Chebyshev polynomial matrices, each (nodes, nodes)

        Returns:
            out: (batch, nodes, out_channels)
        """
        batch_size, n_nodes, _ = x.shape
        out = torch.zeros(batch_size, n_nodes, self.out_channels, device=x.device, dtype=x.dtype)

        for k in range(self.K):
            # T_k(L) @ x: (nodes, nodes) @ (batch, nodes, in_channels) -> (batch, nodes, in_channels)
            Tx = torch.einsum('ij,bjk->bik', cheb_polys[k], x)
            # Tx @ W_k: (batch, nodes, in_channels) @ (in_channels, out_channels)
            out += Tx @ self.weights[k]

        out += self.bias
        return out


class DCGRUCell(nn.Module):
    """
    Diffusion Convolutional Gated Recurrent Unit Cell.

    Gates use diffusion graph convolution instead of standard matrix multiplication.
    """

    def __init__(self, input_dim: int, hidden_dim: int, K: int = 2):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.K = K

        # Reset gate: r = sigmoid(DCG(x) + DCG(h))
        self.dcgru_r = DiffusionGraphConv(input_dim + hidden_dim, hidden_dim, K)
        # Update gate: z = sigmoid(DCG(x) + DCG(h))
        self.dcgru_z = DiffusionGraphConv(input_dim + hidden_dim, hidden_dim, K)
        # Candidate: h~ = tanh(DCG(x) + DCG(r * h))
        self.dcgru_h = DiffusionGraphConv(input_dim + hidden_dim, hidden_dim, K)

    def forward(self, x: torch.Tensor, h: torch.Tensor,
                cheb_polys: List[torch.Tensor]) -> torch.Tensor:
        """
        Args:
            x: (batch, nodes, input_dim)
            h: (batch, nodes, hidden_dim)
            cheb_polys: List of Chebyshev polynomial matrices

        Returns:
            h_new: (batch, nodes, hidden_dim)
        """
        # Concatenate input and hidden state
        xh = torch.cat([x, h], dim=-1)

        # Reset gate
        r = torch.sigmoid(self.dcgru_r(xh, cheb_polys))

        # Update gate
        z = torch.sigmoid(self.dcgru_z(xh, cheb_polys))

        # Candidate hidden state
        xh_r = torch.cat([x, r * h], dim=-1)
        h_candidate = torch.tanh(self.dcgru_h(xh_r, cheb_polys))

        # New hidden state
        h_new = z * h + (1 - z) * h_candidate

        return h_new


class DCGRUEncoder(nn.Module):
    """Encoder: Multi-layer DCGRU"""

    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, K: int = 2):
        super().__init__()
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim

        self.layers = nn.ModuleList()
        for i in range(num_layers):
            in_dim = input_dim if i == 0 else hidden_dim
            self.layers.append(DCGRUCell(in_dim, hidden_dim, K))

    def forward(self, x: torch.Tensor, cheb_polys: List[torch.Tensor],
                hidden: torch.Tensor = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (batch, seq_len, nodes, input_dim)
            cheb_polys: List of Chebyshev polynomial matrices
            hidden: (num_layers, batch, nodes, hidden_dim) or None

        Returns:
            outputs: (batch, seq_len, nodes, hidden_dim)
            hidden: (num_layers, batch, nodes, hidden_dim)
        """
        batch_size, seq_len, n_nodes, _ = x.shape

        if hidden is None:
            hidden = torch.zeros(self.num_layers, batch_size, n_nodes, self.hidden_dim,
                               device=x.device, dtype=x.dtype)

        layer_outputs = []
        new_hidden = []

        for layer_idx, layer in enumerate(self.layers):
            h = hidden[layer_idx]  # (batch, nodes, hidden_dim)
            layer_out = []

            for t in range(seq_len):
                h = layer(x[:, t], h, cheb_polys)
                layer_out.append(h)

            layer_out = torch.stack(layer_out, dim=1)  # (batch, seq_len, nodes, hidden_dim)
            layer_outputs.append(layer_out)
            new_hidden.append(h)

            # Next layer input is this layer's output
            x = layer_out

        new_hidden = torch.stack(new_hidden, dim=0)  # (num_layers, batch, nodes, hidden_dim)
        return x, new_hidden  # Return last layer output and all hidden states


class DCGRUDecoder(nn.Module):
    """Decoder: Multi-layer DCGRU with teacher forcing"""

    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int,
                 output_dim: int, horizon: int, K: int = 2):
        super().__init__()
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim
        self.horizon = horizon
        self.output_dim = output_dim

        self.layers = nn.ModuleList()
        for i in range(num_layers):
            in_dim = input_dim if i == 0 else hidden_dim
            self.layers.append(DCGRUCell(in_dim, hidden_dim, K))

        # Output projection
        self.output_proj = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor, cheb_polys: List[torch.Tensor],
                hidden: torch.Tensor, teacher_forcing_ratio: float = 0.5) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, nodes, input_dim) - encoder output or GO token (batch, nodes, output_dim)
            cheb_polys: List of Chebyshev polynomial matrices
            hidden: (num_layers, batch, nodes, hidden_dim) - from encoder
            teacher_forcing_ratio: Probability of using ground truth as next input

        Returns:
            outputs: (batch, horizon, nodes, output_dim)
        """
        # Handle both 4D (sequence) and 3D (GO token) input
        if x.dim() == 4:
            batch_size, _, n_nodes, _ = x.shape
        else:
            batch_size, n_nodes, _ = x.shape

        outputs = []

        # Initial input: last encoder output or zeros (GO token)
        if x.dim() == 4 and x.size(1) > 0:
            decoder_input = x[:, -1]  # (batch, nodes, input_dim)
        else:
            decoder_input = x  # (batch, nodes, output_dim) - GO token

        for t in range(self.horizon):
            layer_input = decoder_input
            new_hidden = []

            for layer_idx, layer in enumerate(self.layers):
                h = hidden[layer_idx]
                h = layer(layer_input, h, cheb_polys)
                layer_input = h
                new_hidden.append(h)

            hidden = torch.stack(new_hidden, dim=0)

            # Project to output
            out = self.output_proj(layer_input)  # (batch, nodes, output_dim)
            outputs.append(out)

            # Next input: use prediction (or ground truth if teacher forcing)
            decoder_input = out

        return torch.stack(outputs, dim=1)  # (batch, horizon, nodes, output_dim)


class DCRNN(nn.Module):
    """
    Full DCRNN Model for Traffic Forecasting.

    Args:
        input_dim: Number of input features per node
        hidden_dim: Hidden dimension size
        num_layers: Number of DCGRU layers
        output_dim: Number of output features (1 for speed)
        horizon: Prediction horizon (number of future steps)
        K: Chebyshev polynomial order
        cheb_polys: Precomputed Chebyshev polynomials (list of K tensors)
    """

    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2,
                 output_dim: int = 1, horizon: int = 1, K: int = 2,
                 cheb_polys: List[torch.Tensor] = None):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_dim = output_dim
        self.horizon = horizon
        self.K = K

        if cheb_polys is None:
            raise ValueError("Chebyshev polynomials must be provided")

        # Register Chebyshev polynomials as buffers (not parameters)
        for k, poly in enumerate(cheb_polys):
            self.register_buffer(f'cheb_poly_{k}', poly)

        self.encoder = DCGRUEncoder(input_dim, hidden_dim, num_layers, K)
        self.decoder = DCGRUDecoder(output_dim, hidden_dim, num_layers,
                                     output_dim, horizon, K)

    def get_cheb_polys(self) -> List[torch.Tensor]:
        return [getattr(self, f'cheb_poly_{k}') for k in range(self.K)]

    def forward(self, x: torch.Tensor, teacher_forcing_ratio: float = 0.0) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, nodes, input_dim)
            teacher_forcing_ratio: Probability of using ground truth in decoder

        Returns:
            out: (batch, horizon, nodes, output_dim)
        """
        cheb_polys = self.get_cheb_polys()

        # Encode
        _, encoder_hidden = self.encoder(x, cheb_polys)

        # Decode
        # Use zeros as GO token (or last encoder output)
        go_token = torch.zeros(x.size(0), x.size(2), self.output_dim,
                               device=x.device, dtype=x.dtype)
        out = self.decoder(go_token, cheb_polys, encoder_hidden, teacher_forcing_ratio)

        return out


def load_chebyshev_polys(adj: np.ndarray, K: int, device: torch.device) -> List[torch.Tensor]:
    """Compute and convert Chebyshev polynomials to tensors."""
    from training.graph import compute_chebyshev_polynomials
    polys = compute_chebyshev_polynomials(adj, K)
    return [torch.from_numpy(p).float().to(device) for p in polys]


if __name__ == "__main__":
    # Test model instantiation
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # Load adjacency
    from training.graph import load_adjacency_matrix
    adj = load_adjacency_matrix('data/traffic/adjacency_matrix.csv')

    # Compute Chebyshev polynomials
    K = 2
    cheb_polys = load_chebyshev_polys(adj, K, device)

    # Create model
    model = DCRNN(
        input_dim=19,
        hidden_dim=64,
        num_layers=2,
        output_dim=1,
        horizon=1,
        K=K,
        cheb_polys=cheb_polys
    ).to(device)

    # Test forward pass
    batch_size = 4
    seq_len = 7
    n_nodes = 16
    input_dim = 19

    x = torch.randn(batch_size, seq_len, n_nodes, input_dim).to(device)
    out = model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {out.shape}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")