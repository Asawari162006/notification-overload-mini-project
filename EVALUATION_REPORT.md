# Evaluation report

Final corrected run: 2026-10-08. Real data only. Earlier results before the same-second feature fix are superseded. Target, cleaning rules, holdouts and parameter search were unchanged.

There are 43,848 eligible recorded posting-to-removal episodes across 13 distinct traces (14 raw IDs). Trace 7 duplicates trace 6 and is excluded. Unknown removals, conflicting/overlapping identities and invalid order are not training targets. Valid zero and long durations remain.

Selection minimizes development participant-average MAE in original seconds. Grouped validation errors are averaged over participants equally; final tests do not select parameters or models. All models use identical strictly earlier outcome updates, including timestamp-group handling. Dynamic source histories are within participant. The historical baseline falls back to frozen training source/global medians.

## Experiment A: unseen participants

Training/development fit: 37,859 episodes. Final test: 5,989 episodes from 3 participants. Development winner: **random_forest**, parameter 20.

A reserves entire participants with seed 42 and uses three grouped development folds. Test IDs: 1, 14, 9.

| Model | Development mean user MAE | Test mean user MAE | Pooled test MAE | Median AE | RMSE | R² |
|---|---:|---:|---:|---:|---:|---:|
| global_median | 541.27 | 691.38 | 728.79 | 10.00 | 4277.96 | -0.03 |
| historical_median | 547.89 | 689.79 | 727.59 | 15.00 | 4276.19 | -0.03 |
| ridge | 1.48e+30 | 692.49 | 724.18 | 24.88 | 4264.50 | -0.02 |
| random_forest | 516.00 | 670.92 | 707.93 | 22.46 | 4247.25 | -0.01 |
| gradient_boosting | 518.62 | 673.20 | 710.01 | 20.48 | 4252.23 | -0.02 |

All errors above are seconds. Pooled MAE gives frequent users greater weight; mean user MAE weights each participant equally. R² is supplementary and can be negative.

### Per-participant MAE for the selected model

| Participant | Test MAE seconds |
|---|---:|
| 1 | 921.57 |
| 14 | 730.73 |
| 9 | 360.44 |

### Development ablation

Fixed gradient booster, identical manifests; scores average participant MAE within each fold then average folds. These ablations do not select the deployed model.

| Features | Fold-average user MAE seconds | Change from previous |
|---|---:|---:|
| A metadata | 555.21 | — |
| B recent load | 548.99 | -6.22 |
| C source history | 526.33 | -22.66 |
| D personal history | 525.60 | -0.73 |

Negative changes improve MAE; positive changes worsen it. Each feature addition should be judged from these actual values, not assumed helpful.

### Held-out error analysis

| Group | Samples | MAE seconds |
|---|---:|---:|
| unseen_source | 377 | 4169.16 |
| rare_source_training_count_1_to_20 | 195 | 439.85 |
| frequent_source | 5417 | 476.70 |
| sparse_history | 20 | 656.43 |
| missing_context | 0 | — |
| cold_start_user | 4 | 31.15 |
| high_load | 121 | 210.81 |
| (-inf, 4.0] | 2181 | 13.74 |
| (4.0, 543.0] | 2945 | 85.39 |
| (543.0, 7221.78] | 740 | 1677.17 |
| (7221.78, inf] | 123 | 22091.60 |

Duration range boundaries are computed from training only: 4.00, 543.00, 7221.78 seconds. Source frequency groups also use training counts only.

Prediction-versus-observed and signed-residual plots: `artifacts/A_diagnostics.png`. Full event predictions: `artifacts/A_predictions.csv`.

## Experiment B: future notifications for known users

Training/development fit: 35,057 episodes. Final test: 8,776 episodes from 13 participants. Development winner: **random_forest**, parameter 5.

B uses per-participant posting-time 60%/80% boundaries. Training labels must be removed strictly before each fit cutoff. Histories update during replay; model parameters never update on test. Boundary timestamps and episode IDs are saved in the frozen manifest.

| Model | Development mean user MAE | Test mean user MAE | Pooled test MAE | Median AE | RMSE | R² |
|---|---:|---:|---:|---:|---:|---:|
| global_median | 513.15 | 551.20 | 451.17 | 5.00 | 2535.31 | -0.03 |
| historical_median | 510.96 | 548.01 | 449.01 | 9.00 | 2532.29 | -0.03 |
| ridge | 489.69 | 529.31 | 424.05 | 9.01 | 2472.90 | 0.02 |
| random_forest | 476.12 | 514.80 | 409.87 | 10.15 | 2443.42 | 0.04 |
| gradient_boosting | 481.01 | 515.51 | 410.27 | 9.15 | 2468.24 | 0.02 |

All errors above are seconds. Pooled MAE gives frequent users greater weight; mean user MAE weights each participant equally. R² is supplementary and can be negative.

### Per-participant MAE for the selected model

| Participant | Test MAE seconds |
|---|---:|
| 1 | 746.40 |
| 10 | 565.14 |
| 11 | 241.88 |
| 12 | 356.91 |
| 13 | 104.70 |
| 14 | 188.30 |
| 2 | 292.06 |
| 3 | 94.94 |
| 4 | 724.71 |
| 5 | 1235.43 |
| 6 | 1134.25 |
| 8 | 622.62 |
| 9 | 385.05 |

### Development ablation

Fixed gradient booster, identical manifests; scores average participant MAE within each fold then average folds. These ablations do not select the deployed model.

| Features | Fold-average user MAE seconds | Change from previous |
|---|---:|---:|
| A metadata | 484.83 | — |
| B recent load | 480.30 | -4.53 |
| C source history | 478.87 | -1.43 |
| D personal history | 481.60 | 2.73 |

Negative changes improve MAE; positive changes worsen it. Each feature addition should be judged from these actual values, not assumed helpful.

### Held-out error analysis

| Group | Samples | MAE seconds |
|---|---:|---:|
| unseen_source | 22 | 7007.44 |
| rare_source_training_count_1_to_20 | 133 | 1078.84 |
| frequent_source | 8621 | 382.71 |
| sparse_history | 0 | — |
| missing_context | 0 | — |
| cold_start_user | 0 | — |
| high_load | 443 | 40.99 |
| (-inf, 5.0] | 4374 | 9.70 |
| (5.0, 584.4] | 3424 | 94.21 |
| (584.4, 8344.96] | 889 | 1726.45 |
| (8344.96, inf] | 89 | 19069.62 |

Duration range boundaries are computed from training only: 5.00, 584.40, 8344.96 seconds. Source frequency groups also use training counts only.

Prediction-versus-observed and signed-residual plots: `artifacts/B_diagnostics.png`. Full event predictions: `artifacts/B_predictions.csv`.

## Search, deployment and limitations

Search: Ridge alpha 1/10; Random Forest minimum leaf size 5/20 (60 trees, max depth 12); histogram gradient boosting L2 1/10 (100 iterations, 15 leaves). All three regressors fit log1p targets and inverse-transform predictions. Negative predictions are clamped to zero. Imputation, encoding, scaling and target transformation fit within each training fold. Unknown source encoding and missing-history fallback are explicit.

The deployed model is the B development-fit winner; the final B test is still held out. A baseline may legitimately win in another dataset. A Ridge validation error is extremely large under unseen-user extrapolation; it is retained transparently and was not selected. No fabricated accuracy or confidence percentage is reported.

The sample is selected on observed, unambiguous recorded removal. No verified monitoring endpoints, Android tags, removal reasons or local timezones exist. Recorded posting may be a later update rather than first lifecycle posting. The population has only 13 distinct traces and A tests only three participants: notifications are not independent people. Per-participant results show variability but are not a confidence interval or proof of broad generalization. Long-duration errors remain substantial. Feature association is not causality.

Unusual load uses a B-training 95th-percentile posting-count threshold; there are no anomaly labels or anomaly accuracy. Removal is not reading, attention or importance; unusual load is not fatigue. Synthetic simulator data never enters evaluation. Optional horizon classification and survival analysis are deferred for lack of verified follow-up.

Full audit, search fold metrics, manifests and metadata remain available in `artifacts/audit.json`, `evaluation.json`, `splits.json` and `model_metadata.json`.
