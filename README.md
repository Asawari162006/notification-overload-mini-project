# Notification Overload Analysis and Removal Time Prediction System

Runnable undergraduate mini project: React/Vite/TypeScript, FastAPI/Pydantic, pandas/NumPy/scikit-learn, SQLAlchemy/SQLite. No paid API, GPU or phone permission is required. The website controls only its own simulation queues.

## Windows PowerShell
Run from this project directory. Python 3.11–3.13 and Node 20.19+ are supported.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv\Scripts\python.exe -m ml.pipeline download
.venv\Scripts\python.exe -m ml.pipeline audit
.venv\Scripts\python.exe -m ml.pipeline reconstruct
.venv\Scripts\python.exe -m ml.pipeline features
.venv\Scripts\python.exe -m ml.pipeline splits
.venv\Scripts\python.exe -m ml.pipeline train
.venv\Scripts\python.exe -m ml.pipeline evaluate
npm --prefix frontend run build
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. Production assets are served by FastAPI; all screen navigation is client-side. `reconstruct` repeats the audit and reconstruction together. `evaluate` displays the saved held-out evaluation computed during training. `all` runs download → audit → features → splits → training/evaluation. Data commands overwrite generated outputs, never the unchanged archive.

`requirements.lock.txt` pins the tested Python dependency closure; `requirements.txt` records the primary dependencies. To run browser checks on Windows, use `npm --prefix frontend run test:e2e` with the production server running; the config uses the installed Edge executable. On Linux/macOS, run `cd frontend` then `npx playwright install chromium` before `npm run test:e2e`. Browser screenshots and JSON results are saved under `artifacts/`.

For development, run the backend as above and `npm --prefix frontend run dev` in a second terminal. Visit http://127.0.0.1:5173. Vite proxies `/api` to port 8000. Restart the backend after training or rebuilding production assets; it loads trusted artifacts at startup.

## Linux/macOS alternative

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv/bin/python -m ml.pipeline all
npm --prefix frontend run build
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Cross-platform import: copy the original `ami2018_notifications.sql.zip` into `data/raw/` and run `audit`, `features`, `splits`, `train`. Do not execute the SQL against any database. Only values in the documented INSERT format are parsed, with size/schema checks; alternative CSV data requires an explicit adapter rather than guessed units. A template is provided in `data/templates/episode_import.csv` for documenting normalized records.

## Tests and deterministic demo

```powershell
.venv\Scripts\python.exe -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build
.venv\Scripts\python.exe scripts\smoke.py
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/simulator/seed
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/simulator/reset
```

Seed/reset affects only the local simulator database. Seed creates four explicitly synthetic items: protected emergency and three items for a digest at virtual time 300. Advance the clock to see the digest, or change preferences to demonstrate deadline precedence. Historical replay preserves event order and calls the same feature logic; it can copy events into the policy simulator without changing observed removal outcomes. Reset before switching between historical epoch times and a synthetic clock starting at zero.

See `docs/demo_script.md`, `TEST_REPORT.md`, `docs/viva_guide.md`, and `docs/architecture.md`. API docs: http://127.0.0.1:8000/docs.

## Research meaning

The target is **recorded removal timestamp minus recorded posting timestamp**, in seconds. It does not establish reading, attention, importance or complete lifecycle duration. Zero removal is unknown. Exact posting identities are consolidated; conflicting/overlapping identities are excluded and raw serial lineage retained. IDs 6 and 7 have identical traces; ID 7 is excluded from supervised data. Valid zero and long durations remain.

A uses entire held-out participants with grouped development CV. B uses per-participant chronological boundaries and training labels observed before each cutoff. Dynamic histories update only when prior removals become observable, identically for every model. Model selection minimizes development participant-average MAE; pooled metrics are also reported. A and B are separate deployment questions and can select different winners. The deployed artifact is B's development-fit winner, retaining the final test holdout.

A historical 95th-percentile load threshold is fitted only on B training periods. It flags **unusual notification load**, without anomaly accuracy or fatigue claims. Preference rules, rather than removal predictions, control simulator delivery. No auto-suppression occurs.

## Data and local artifacts

Source: https://github.com/komis1/ami2018-notifications. Preserve its GPL-3.0 license and academic citation (see `DATA_FEASIBILITY.md`). `data/raw/` holds unchanged archive/docs; `data/processed/` holds records, canonical episode lineage, eligible episodes and features. `artifacts/` holds actual audit, frozen manifests, evaluation, predictions, diagnostic PNGs and trusted local joblib pipeline plus metadata/checksums. Raw data, database, environment and generated artifacts are ignored by Git. Do not load joblib files from untrusted sources: checksum validates accidental change, not trust in an external publisher.

Missing or invalid artifacts produce explicit unavailable states; synthetic data never trains or validates a model. Optional classification and survival analysis are deferred because verified follow-up endpoints are unavailable. Dataset selection and limited participant population are material research limitations.

Future hackathon scope, deliberately absent: interactive what-if explorer, dedicated input-quality guard dashboard, exportable experiment cards, and model-disagreement interface.
