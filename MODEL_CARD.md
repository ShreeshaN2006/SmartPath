# DCRNN Traffic Forecasting Model Card

## Model Details

### Model Information
- **Name**: SmartPath DCRNN
- **Version**: 1.0
- **Type**: Diffusion Convolutional Recurrent Neural Network
- **Task**: Daily Average Speed Forecasting (Regression)
- **Architecture**: Encoder-Decoder with DCGRU cells + Diffusion Graph Convolution
- **Framework**: PyTorch 2.3.1
- **License**: MIT

### Training Configuration
| Parameter | Value |
|-----------|-------|
| Input Sequence Length | 7 days |
| Prediction Horizon | 1 day |
| Hidden Dimension | 64 |
| Number of Layers | 2 |
| Chebyshev Order (K) | 2 |
| Batch Size | 16 |
| Learning Rate | 0.001 |
| Optimizer | Adam |
| Loss Function | MSE |
| Epochs Trained | 5 (demo) / 100+ (recommended) |
| Early Stopping | Patience 10 |
| LR Scheduler | ReduceLROnPlateau (factor=0.5, patience=5) |
| Gradient Clipping | max_norm=1.0 |

---

## Intended Use

### Primary Use Case
Predict next-day average traffic speed for 16 Bangalore intersections to support route optimization in the SmartPath platform.

### Target Users
- SmartPath routing engine (backend)
- Traffic analysts
- Logistics/fleet operators in Bangalore

### Input
- 7 days of historical traffic features (19 features × 16 nodes)
- Graph adjacency matrix (16×16, row-normalized)

### Output
- Next-day Average Speed prediction (km/h) for all 16 nodes

---

## Training Data

### Dataset
**SmartPath Daily Traffic Dataset** (synthetic, not real-world)

| Attribute | Value |
|-----------|-------|
| Source | `data/traffic/smartpath_traffic_model_ready.csv` |
| Time Range | 2022-01-01 to 2024-08-09 |
| Frequency | Daily |
| Nodes | 16 intersections |
| Areas | 8 Bangalore zones |
| Samples | 8,936 observations |
| Split | Chronological 70/15/15 |

### Features (19)
- Traffic Volume, Average Speed, Congestion Level, Incident Reports
- Environmental Impact, Public Transport Usage, Traffic Signal Compliance
- Parking Usage, Pedestrian/Cyclist Count
- Day of week, Month, Is Weekend
- Weather Code (encoded), Roadwork Code (encoded)
- Lag-1: Speed, Volume, Congestion
- Rolling: Speed 3-day, Speed 7-day

### Preprocessing
1. Forward-fill missing lag features with 0
2. Label encode categorical (Weather, Roadwork)
3. Create continuous date range (952 days), forward/backward fill per node
4. Chronological split: 70% train / 15% val / 15% test
5. StandardScaler fitted on train only (features + target)

---

## Graph Structure

### Provisional Adjacency Matrix (16×16)
**Construction Method**: Area-based + known corridors (NOT real GPS coordinates)

| Connection Type | Weight | Examples |
|-----------------|--------|----------|
| Self-loop | 1.0 | All nodes |
| Same area | 1.0 | Hosur Rd ↔ Silk Board (Electronic City) |
| Known corridors | 0.5 | Silk Board → Sony World (ORR) |

**Note**: This is a **provisional graph**. Replace with real road-network adjacency when GPS coordinates available.

---

## Evaluation Results

### Test Set Metrics (Horizon=1)

| Model | MAE (km/h) | RMSE (km/h) | MAPE (%) | R² |
|-------|------------|-------------|----------|-----|
| **DCRNN** | **7.35** | **9.52** | **21.12** | **0.231** |
| RandomForest | 7.47 | 9.66 | 21.43 | 0.207 |
| XGBoost | 7.85 | 10.11 | 22.50 | 0.132 |
| Naive Previous-Day | 6.96 | 11.42 | 19.45 | -0.107 |
| Historical Mean | 8.62 | 10.71 | 24.89 | 0.026 |
| Ridge | 11.36 | 14.16 | 31.60 | -0.703 |

### Per-Node Performance (DCRNN)
| Node | MAE | RMSE | MAPE | R² |
|------|-----|------|------|-----|
| Hosur Road | ~7.2 | ~9.1 | ~20% | ~0.25 |
| Silk Board Junction | ~7.5 | ~9.8 | ~22% | ~0.22 |
| Ballari Road | ~6.8 | ~8.9 | ~18% | ~0.30 |
| Hebbal Flyover | ~7.1 | ~9.3 | ~21% | ~0.24 |
| 100 Feet Road | ~7.4 | ~9.5 | ~22% | ~0.21 |
| CMH Road | ~7.0 | ~9.0 | ~19% | ~0.28 |
| Jayanagar 4th Block | ~7.6 | ~9.7 | ~23% | ~0.18 |
| South End Circle | ~7.3 | ~9.4 | ~21% | ~0.23 |
| Sarjapur Road | ~7.5 | ~9.6 | ~22% | ~0.20 |
| Sony World Junction | ~7.4 | ~9.5 | ~22% | ~0.21 |
| Anil Kumble Circle | ~7.7 | ~9.8 | ~24% | ~0.17 |
| Trinity Circle | ~7.2 | ~9.2 | ~20% | ~0.26 |
| ITPL Main Road | ~6.5 | ~8.5 | ~17% | ~0.33 |
| Marathahalli Bridge | ~7.6 | ~9.7 | ~23% | ~0.19 |
| Tumkur Road | ~7.1 | ~9.3 | ~21% | ~0.24 |
| Yeshwanthpur Circle | ~7.5 | ~9.6 | ~22% | ~0.21 |

---

## Limitations

### Critical Limitations
1. **Daily Resolution Only**: Model trained on daily data. **NOT suitable for real-time 5-min/15-min/hourly predictions.**
2. **Provisional Graph**: Adjacency matrix based on area proximity, not real road distances or connectivity.
3. **Synthetic Data**: Dataset is generated, not collected from real traffic sensors.
3. **Short History**: 7-day input may miss weekly/seasonal patterns.
4. **Single Horizon**: Primarily validated on 1-day forecast.

### Known Data Issues
- No common dates across all 16 nodes (different date ranges/gaps)
- Some nodes have sparse data (< 300 days): Hosur Rd, Silk Board, ITPL, Tumkur, Yeshwanthpur
- Forward-fill creates temporal autocorrelation
- Lag features NaN-filled with 0 at series start

### Model Limitations
- Single-output (Average Speed only); Congestion/Volume not jointly predicted
- No uncertainty quantification (no prediction intervals)
- Teacher forcing decay may cause exposure bias
- No explicit handling of holidays/special events

---

## Ethical Considerations

- **No PII**: Traffic data contains no personal information
- **No Bias Amplification**: Model predicts aggregate speeds, not individual behavior
- **Transparency**: Provisional graph and synthetic data clearly documented
- **No Deployment Guarantee**: Model is research prototype, not certified for safety-critical use

---

## Deployment Requirements

### Inference Pipeline
```python
# Load model
model = DCRNN(config).to(device)
model.load_state_dict(torch.load('models/dcrnn/best_model.pt'))

# Load scalers
feature_scaler = joblib.load('models/scalers/feature_scaler.pkl')
target_scaler = joblib.load('models/scalers/target_scaler.pkl')

# Prepare sequence (last 7 days)
X_scaled = prepare_latest_sequence(...)

# Predict
preds = model(torch.FloatTensor(X_seq).to(device))
preds_orig = target_scaler.inverse_transform(preds)
```

### Hardware
- CPU: ~150ms per batch (16 samples)
- GPU: ~30ms per batch
- Memory: < 500MB

### API Interface (Planned)
```
POST /api/traffic/forecast
{
  "horizon": 1,
  "nodes": ["Hosur Road", "Silk Board Junction", ...]
}
→ { "predictions": [...], "timestamp": "..." }
```

---

## Performance Monitoring

### Recommended Metrics to Track
- MAE/RMAPE per node per week
- Prediction latency (p95 < 200ms)
- Data freshness (max age of input features)
- Drift detection (feature distribution shift)

### Retraining Schedule
- Monthly retraining recommended
- Trigger: MAE increase > 15% from baseline
- Automated pipeline: weekly data pull → retrain → validate → deploy

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial release: DCRNN with provisional graph, daily data, 1-day horizon |

---

## References

1. Li, Y., Yu, R., Shahabi, C., & Liu, Y. (2018). "Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting." *ICLR 2018*.
2. SmartPath Project: https://github.com/ShreeshaN2006/SmartPath

---

## Disclaimer

> **This model demonstrates predictive traffic forecasting at daily resolution using a synthetic dataset and provisional graph. It should not be represented as a production-grade real-time traffic prediction system. Higher-frequency traffic data and real road-network connectivity would be required for operational deployment.**

---

*Model Card Version: 1.0 | Generated: 2024 | SmartPath DCRNN*