# Test report

Final verification on 2026-10-08, Windows, Python 3.13.9, Node 20.20.2. All results below were executed; notebook cells are illustrative and were not executed as a separate test suite.

| Command / check | Actual result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` | 19 passed in 18.35 seconds |
| `npm --prefix frontend test` | 5 passed |
| `npm --prefix frontend run build` | TypeScript and Vite production build passed |
| `npm --prefix frontend run test:e2e` | 2 passed: full research/prediction/replay/simulator flow and 390px narrow layout |
| `npm --prefix frontend audit` | 0 known vulnerabilities |
| `.venv\Scripts\python.exe scripts\smoke.py` | Passed against live FastAPI server with corrected trained artifact |
| Real SQL archive audit, reconstruction, features, frozen splits, training/evaluation | Executed successfully; 43,848 eligible episodes, 13 distinct traces |
| Desktop and narrow screenshot inspection | Inspected screenshots for overview, simulator and prediction; layout readable, no body horizontal overflow at 390px |

Coverage includes seconds/duration validation, zero and missing/invalid outcomes, conservative identities and duplicates, exact duplicate participant traces, strictly earlier outcomes, simultaneous posting feature parity, chronological label availability, participant separation, fold-only preprocessing, training/inference parity (including real cache), unseen sources/missing history, hand-verifiable metrics, missing/corrupt artifacts, API validation, persistent queue restart, idempotent delivery, protected bypass, deadline ties, digest originals, clock monotonicity and synthetic/research isolation.

The live smoke demo verified unchanged real-data counts, dataset checksum, both experiments, a 17.7862-second new-user/unseen-source prediction with explicit fallbacks, 22,093 unusual posting cutoffs for participant 1 under the training reference, three replay records, and four synthetic items delivered with two simulated alerts. These are software outcomes, not evidence of improved human attention or fatigue.

Earlier failures were corrected: slow reconstruction, a TypeScript brace, locale-sensitive assertions, queue-order assumptions, vulnerable development dependencies, stale-page rendering, test-selector/discovery issues and simultaneous posting history. The corrected ML run reused the frozen target/exclusions/splits/search; earlier metrics are superseded. Group-CV selection aggregates all participant validation errors equally, rather than averaging unequal-sized folds. Reserved hackathon screens remain absent. In-app browser attachment failed; isolated Edge browser tests supplied the verified UI evidence.

Artifacts: `artifacts/browser-results.json`, screenshots, `smoke.json`, `evaluation.json`, model metadata and held-out prediction CSVs. Generated artifacts and raw data are excluded from Git. The UI and backend run locally with one Uvicorn worker and explicit virtual-clock scheduling; distributed scheduling is outside scope.
