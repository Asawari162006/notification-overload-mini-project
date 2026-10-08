# Reproducible demonstration

1. Run README startup commands; open Overview. Confirm real dataset and actual trained model status. If unavailable, inspect the reason rather than claim training succeeded.
2. Open Dataset audit. Show archive SHA-256, citation/license, unknown-removal counts, exact duplicate trace 7→6, exclusions and actual SQL schema. Explain recorded episodes and incomplete follow-up.
3. Open Model comparison. Switch between A and B; show both median baselines and three regressors, development selection objective, held-out metrics, per-participant MAE and ablations. Valid long durations remain.
4. Open Prediction. Use default new-user/source context; submit. Show estimate in seconds/minutes, model version and no-history/unseen-source fallback. Try missing device context. A prediction is not confidence or importance.
5. Open Load analysis; choose a participant with unusual periods. Compare counts with the training-only reference and threshold. No fatigue or anomaly accuracy is measured.
6. Open Historical replay. Play, pause, next-event and restart page controls use real event order and virtual time. Observed outcomes are distinct from predictions. A policy copy keeps the original historical outcome unchanged; reset queues before changing clock origin.
7. Open Management simulator. Click Reset + seed synthetic demo. Emergency is protected; three other items wait. Advance 5 minutes; see one digest and expand original items. Refresh or restart backend to demonstrate persistence. Reingest the same key to demonstrate idempotence.
8. Set maximum delay to 60 seconds and digest interval to 300 in Preferences. Ingest a fresh item; advance 1 minute to show deadline precedence. Manual deliver-now does not cause later repeat delivery.
9. Open Model card. Explain removal ≠ reading, unusual load ≠ fatigue, sample selection and the 13 distinct recorded traces. Policy alert counts and queue delays are software outcomes, not human benefits.

Automated API demonstration: `.venv\Scripts\python.exe scripts\smoke.py` while the local production server runs. It reads research endpoints, requests a prediction, seeds/advances synthetic queues and records assertions; it never modifies real research data.
