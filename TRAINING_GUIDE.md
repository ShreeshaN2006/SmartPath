# SmartPath DCRNN Training Guide

## Overview

This guide documents the complete pipeline for training a Diffusion Convolutional Recurrent Neural Network (DCRNN) for traffic speed forecasting using the SmartPath dataset.

---

## Dataset Description

### Source Files
- `data/traffic/smartpath_traffic_model_ready.csv` - Main dataset with 8,936 daily observations
- `data/traffic/smartpath_traffic_sequence_ready.csv` - Sequence-ready version (8,825 rows)
- `data/traffic/traffic_nodes.csv` - 16 traffic node definitions (no coordinates provided)

### Key Statistics
- **Time Range**: 2022-01-01 to 2024-08-09 (952 days)
- **Nodes**: 16 traffic locations across 8 Bangalore areas
- **Frequency**: Daily (NOT high-frequency 5-min/15-min/hourly data)
- **Primary Target**: Average Speed (km/h)

### Areas and Nodes
| Area | Nodes |
|------|-------|
| Electronic City | Hosur Road, Silk Board Junction |
| Hebbal | Ballari Road, Hebbal Flyover |
| Indiranagar | 100 Feet Road, CMH Road |
| Jayanagar | Jayanagar 4th Block, South End Circle |
| Koramangala | Sarjapur Road, Sony World Junction |
| M.G. Road | Anil Kumble Circle, Trinity Circle |
| Whitefield | ITPL Main Road, Marathahalli Bridge |
| Yeshwanthpur | Tumkur Road, Yeshwanthpur Circle |

### Features (19 selected)
**Traffic**: Traffic Volume, Average Speed, Congestion Level, Incident Reports
**Weather**: Weather Conditions (encoded), Environmental Impact
**Temporal**: day_of_week, month, is_weekend
**Roadwork**: Roadwork and Construction Activity (encoded)
**Lag features (1-day)**: speed_lag_1d, volume_lag_1d, congestion_lag_1d
**Rolling features**: speed_rolling_3d, speed_rolling_7d

---

## Preprocessing Pipeline

### 1. Data Loading & Validation
- Load CSV, parse dates
- Check for duplicates (Date, Road pairs)
- Log missing values, date gaps per node

### 2. Feature Engineering
- Drop redundant: Travel Time Index, Road Capacity Utilization, longer lags (2d, 3d, 7d), quarter
- Fill NaN in lag/rolling features with 0
- Label encode categorical: Weather Conditions, Roadwork

### 3. Synchronization (Critical Step)
**Problem**: Nodes have different date ranges and gaps (no common dates across all 16 nodes)

**Solution**: Create complete date range (2022-01-01 to 2024-08-09 = 952 days)
- Pivot each feature to (date × node) matrix
- Reindex to complete date range
- Forward-fill then backward-fill per node
- Stack features → (952 days × 16 nodes × 19 features)

### 4. Chronological Split (No Random Shuffle)
- **Train**: 70% = 666 days (2022-01-01 to 2023-10-28)
- **Validation**: 15% = 143 days (2023-10-29 to 2024-03-19)
- **Test**: 15% = 143 days (2024-03-20 to 2024-08-09)

### 5. Normalization (Train-Only Fit)
- StandardScaler on features (fit on train, apply to all)
- StandardScaler on target (Average Speed)
- Save scalers: `models/scalers/feature_scaler.pkl`, `target_scaler.pkl`

### 6. Sequence Generation
- Input: 7 days → Predict: 1 day (configurable)
- Sequences: (n_samples, 7, 16, 19) → (n_samples, 1, 16)
- Train: 659, Val: 136, Test: 136 sequences

---

## Graph Construction (Provisional)

**Constraint**: Original dataset has no GPS coordinates for traffic nodes

**Approach**: Area-based provisional adjacency
- Same-area nodes: weight 1.0 (strong connection)
- Known corridor connections: weight 0.5 (e.g., Silk Board → Sony World via ORR)
- Self-loops: 1.0
- Row-normalized for diffusion convolution

**Files**:
- `data/traffic/adjacency_matrix.csv` - Normalized (row-stochastic)
- `data/traffic/adjacency_matrix_raw.csv` - Unnormalized reference

**Note**: Replace with real road-network adjacency when coordinates available.

---

## DCRNN Architecture

### Model Configuration
```
Input: (batch, 7, 16, 19)
Encoder: 2-layer DCGRU, hidden=64, K=2 Chebyshev polynomials
Decoder: 2-layer DCGRU, output=1 (Average Speed), horizon=1
Parameters: ~156K
```

### Key Components
1. **DiffusionGraphConv**: Implements Chebyshev polynomial diffusion
   - T₀ = I, T₁ = L, Tₖ = 2L·Tₖ₋₁ - Tₖ₋₂
   - L = scaled Laplacian = (2/λ_max)L - I

2. **DCGRUCell**: GRU with diffusion convolution instead of matrix multiply
   - Reset gate: r = σ(DCG([x,h]))
   - Update gate: z = σ(DCG([x,h]))
   - Candidate: h̃ = tanh(DCG([x, r⊙h]))
   - Output: h = z⊙h + (1-z)⊙h̃

3. **Encoder**: Stack of DCGRU layers, processes 7-day sequence
4. **Decoder**: Stack of DCGRU layers, autoregressive with teacher forcing

### Training Details
- Loss: MSE
- Optimizer: Adam (lr=0.001)
- Batch size: 16
- Epochs: 5 (demo), 100+ recommended
- Early stopping: patience=10
- LR scheduler: ReduceLROnPlateau (factor=0.5, patience=5)
- Gradient clipping: max_norm=1.0
- Teacher forcing decay: 0.5 × 0.95^epoch

---

## Reproducing Training

### Prerequisites
```bash
pip install -r requirements.txt
```

### Quick Demo (5 epochs)
```bash
python -m training.train_dcrnn \
    --epochs 5 \
    --batch-size 16 \
    --seq-len 7 \
    --horizon 1 \
    --hidden-dim 64 \
    --num-layers 2 \
    --K 2
```

### Full Training (Recommended)
```bash
python -m training.train_dcrnn \
    --epochs 100 \
    --batch-size 32 \
    --seq-len 7 \
    --horizon 1 \
    --hidden-dim 64 \
    --num-layers 2 \
    --K 2 \
    --patience 15 \
    --lr-scheduler
```

### Experiment Variations
```bash
# 7-day history → 3-day forecast
python -m training.train_dcrnn --seq-len 7 --horizon 3

# 14-day history → 1-day forecast
python -m training.train_dcrnn --seq-len 14 --horizon 1

# 14-day history → 7-day forecast
python -m training.train_dcrnn --seq-len 14 --horizon 7
```

---

## Running Baselines

```bash
python -m training.run_baselines
```

Outputs:
- `results/baseline_results.csv` - Overall metrics
- `results/baseline_*_per_node.csv` - Per-node metrics
- `results/baseline_*_per_horizon.csv` - Per-horizon metrics
- `results/model_comparison.csv` - Combined comparison

---

## Running Inference

```bash
# 1-day forecast
python -m prediction.predict --horizon 1 --output predictions/latest_speed_predictions.csv

# 3-day forecast
python -m prediction.predict --horizon 3

# 7-day forecast
python -m prediction.predict --horizon 7
```

Output: `predictions/latest_speed_predictions.csv`
```
prediction_date,horizon_day,node_id,Road/Intersection Name,predicted_average_speed
2024-08-10,1,0,Hosur Road,33.10
...
```

---

## Generating Visualizations

```bash
python prediction/visualize.py
```

Outputs to `results/plots/`:
- `training_history.png` - Train/val loss curves + LR
- `actual_vs_predicted.png` - Scatter + residuals
- `per_node_comparison.png` - Per-node MAE/RMSE bars
- `per_horizon_comparison.png` - Metrics vs horizon
- `model_comparison.png` - Overall model comparison
- `prediction_examples.png` - Time series for 6 nodes
- `error_distribution.png` - Error histograms

---

## Output Structure

```
SmartPath/
├── data/
│   └── traffic/
│       ├── smartpath_traffic_model_ready.csv
│       ├── smartpath_traffic_sequence_ready.csv
│       ├── traffic_nodes.csv
│       ├── adjacency_matrix.csv
│       └── adjacency_matrix_raw.csv
├── models/
│   ├── dcrnn/
│   │   ├── best_model.pt
│   │   ├── final_model.pt
│   │   └── config.json
│   └── scalers/
│       ├── feature_scaler.pkl
│       ├── target_scaler.pkl
│       ├── categorical_encoders.pkl
│       ├── feature_cols.pkl
│       └── node_names.pkl
├── training/
│   ├── train_dcrnn.py
│   ├── run_baselines.py
│   ├── preprocessing.py
│   ├── dcrnn.py
│   ├── dataset.py
│   ├── evaluation.py
│   └── baselines.py
├── prediction/
│   ├── predict.py
│   └── visualize.py
├── results/
│   ├── plots/
│   ├── baseline_results.csv
│   ├── dcrnn_results.csv
│   ├── model_comparison.csv
│   ├── baseline_*_per_node.csv
│   ├── dcrnn_per_node.csv
│   ├── baseline_*_per_horizon.csv
│   └── dcrnn_per_horizon.csv
├── predictions/
│   └── latest_speed_predictions.csv
└── requirements.txt
```

---

## Key Implementation Notes

### Data Integrity Rules Followed
1. ✅ No fabricated missing values
2. ✅ No fabricated GPS coordinates
3. ✅ No fabricated road-network relationships
4. ✅ No random dataset splitting (chronological only)
5. ✅ No future information leakage (scalers fit on train only)
6. ✅ Clear distinction: actual dataset vs. generated features
7. ✅ No fabricated real-world claims (dataset provenance documented)
8. ✅ Provisional graph clearly documented
9. ✅ Daily data limitation explicitly stated

### Limitations
1. **Daily resolution**: Not suitable for real-time 5-min/15-min predictions
2. **Provisional graph**: Area-based, not real road connectivity
3. **Limited nodes**: Only 16 locations
4. **Short horizon**: Tested on 1-day forecast primarily
5. **Synthetic baselines**: Random Forest/XGBoost with reduced params for speed

### Future Improvements
- Integrate real GPS coordinates for graph
- Higher-frequency data (hourly/15-min)
- DCRNN with attention mechanism
- Multi-horizon loss weighting
- Ensemble methods
- Real-time data pipeline integration

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| NaN loss | Check data preprocessing, reduce LR, increase gradient clipping |
| OOM on GPU | Reduce batch size, use gradient accumulation |
| Slow training | Reduce hidden_dim, num_layers, or use CPU with smaller batch |
| Import errors | Run from project root: `python -m training.train_dcrnn` |
| Config missing keys | Use `config.get('key', default)` pattern |

---

## Contact & References

- **Paper**: "Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting" (Li et al., ICLR 2018)
- **Implementation**: PyTorch custom (no PyG-Temporal dependency)
- **Dataset**: SmartPath synthetic daily traffic data (not real-world)

---

*Last Updated: 2024 | SmartPath DCRNN v1.0*