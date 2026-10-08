# Viva guide

**Problem:** quantify observed notification patterns and predict recorded posting-to-removal duration. We analyze overload as counts and bursts, not a mental fatigue label.

**Target:** duration_seconds = removed_at − posted_at for eligible reconstructed posting episodes. Removal can be automatic, system-triggered or user-triggered; it does not prove reading or importance. Stored timestamps are seconds, despite the linked Android API using milliseconds.

**Dataset:** AmI-2018 public SQL, 176,195 rows and 14 participant IDs. IDs 6/7 have identical traces. The retained sample has selection bias because unknown removal and ambiguous updates are excluded. Monitoring endpoints, Android tags, removal reasons and local timezones are unavailable. Missing removal cannot safely become zero duration or a negative horizon label. Censoring is not established, so survival analysis is deferred.

**Features:** programmed priority, source and device context; previous 5/15/30-minute counts, distinct sources, gap since prior event, historical load deviation, previous source/user outcome medians and missing-history flags. Participant ID is never a predictor. Source histories are within user. New categories use unknown encoding or baseline fallback; missing history uses fold-fitted imputation. We omitted calendar features without local timezone evidence.

**Algorithms:** global training median, online historical median, Ridge, Random Forest and sklearn histogram gradient boosting. Three regressors use log1p target and inverse-transform to seconds. Preprocessing and target fitting occur within training folds. Negative predictions are clamped to zero and API fallbacks disclosed. Participant-average MAE selects the winner on development data.

**Leakage prevention:** current/future removal never enters current features. A prior posting's eventual outcome is usable only after its removal is strictly earlier than the cutoff. Grouped CV and held-out users isolate A. Chronological fits in B exclude labels not available at the fit cutoff. Identical participant traces cannot cross splits. Final test does not select models or cleaning rules. Online historical updates are identical for all models and are disclosed; model parameters remain frozen.

**Metrics:** MAE is mean absolute error; median AE measures a typical event; RMSE emphasizes large errors; R² compares squared error to predicting the evaluation mean and can be negative. Pooled event MAE weights frequent users more; average participant MAE gives each user equal weight. No regression accuracy percentage exists. Notifications are not independent people, and only a small population was observed. Training-derived duration bins and source-frequency groups expose failures.

**Ablation:** fixed gradient boosting with metadata, recent load, source history, then personal history on identical development manifests. Additions can help or harm; inspect actual results. Predictive importance and association do not prove causality.

**Optional classification:** deferred. A valid horizon task needs positive observed removal within a frozen horizon, negatives with proven full-horizon follow-up, and unknown labels otherwise. If feasible, use precision, recall, F1, average precision, balanced accuracy, prevalence and confusion matrix; choose threshold on development data, preserve group/time separation and never oversample before splitting.

**Unusual load:** the previous 15-minute posting count exceeds a 95th-percentile training reference. There are no anomaly labels, so no detector accuracy is claimed. Unusual load is not fatigue.

**Simulator:** protected sources bypass grouping; digest intervals and finite delay bounds control local queues. Deadline-before-digest precedence and idempotent state survive restarts. Predicted long removal times never suppress a notification. Alert counts and delays do not prove changes to human behaviour, attention or fatigue.

**Future work:** obtain verified lifecycle tags and observation endpoints, validate across more participants, and later consider the four reserved hackathon features. They are intentionally absent here.
