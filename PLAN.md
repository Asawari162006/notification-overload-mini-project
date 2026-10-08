# Implementation plan
1. Retrieve and safely parse the real SQL archive; record provenance and feasibility before training.
2. Reconstruct conservative episodes, preserve lineage, and build cutoff-safe shared features.
3. Freeze unseen-participant and chronological experiments; compare baselines, Ridge, Random Forest and gradient boosting with participant-average MAE.
4. Implement FastAPI, SQLite queues, artifact validation and analysis endpoints.
5. Integrate React screens and accessible charts.
6. Implement persistent deterministic grouping simulator and historical replay.
7. Execute tests, builds and smoke checks; document evidence and create local Git checkpoint.

Reserved hackathon features are excluded. Optional classification is deferred unless follow-up validity is established.
