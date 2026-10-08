import { useEffect, useState, useRef } from "react";
import { api, formatSeconds } from "./api";
// JSON endpoints are deliberately visible to undergraduate readers.
type Data = Record<string, any>;
const pages = [
  "Overview",
  "Dataset audit",
  "Exploratory analysis",
  "Model comparison",
  "Prediction",
  "Historical replay",
  "Load analysis",
  "Management simulator",
  "Preferences",
  "Model card",
];
const num = (n: number | undefined) =>
  n === undefined
    ? "—"
    : n.toLocaleString("en-US", { maximumFractionDigits: 1 });
function Badge({ children }: { children: React.ReactNode }) {
  return <span className="badge">{children}</span>;
}
function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: React.ReactNode;
  detail: string;
}) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
export function Bars({
  rows,
  label,
  value,
  title,
}: {
  rows: Data[];
  label: string;
  value: string;
  title: string;
}) {
  const max = Math.max(1, ...rows.map((x) => Number(x[value])));
  return (
    <section className="panel">
      <h3>{title}</h3>
      {!rows.length ? (
        <p>No data available.</p>
      ) : (
        <div className="bars" role="img" aria-label={title}>
          {rows.map((r, i) => (
            <div className="bar-row" key={i}>
              <span title={String(r[label])}>{r[label]}</span>
              <div className="bar-track">
                <div
                  style={{ width: `${Math.max(1, (r[value] / max) * 100)}%` }}
                />
              </div>
              <b>{num(r[value])}</b>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
function Plot({
  rows,
  x,
  y,
  title,
}: {
  rows: Data[];
  x: string;
  y: string;
  title: string;
}) {
  if (!rows.length)
    return (
      <section className="panel">
        <h3>{title}</h3>
        <p>No plotted observations.</p>
      </section>
    );
  const timeAxis = x === "time";
  const minx = timeAxis ? Math.min(...rows.map((r) => r[x])) : 0;
  const maxx = Math.max(
    1,
    ...rows.map((r) => (timeAxis ? r[x] - minx : Math.log1p(Math.abs(r[x])))),
  );
  const maxy = Math.max(1, ...rows.map((r) => Math.log1p(Math.abs(r[y]))));
  return (
    <section className="panel">
      <h3>{title}</h3>
      <svg
        viewBox="0 0 560 230"
        role="img"
        aria-label={`${title}; ${timeAxis ? "UTC time on horizontal axis" : "log-scaled horizontal axis"}; log-scaled vertical axis`}
      >
        <line x1="35" y1="200" x2="540" y2="200" stroke="#a6b9b0" />
        <line x1="35" y1="10" x2="35" y2="200" stroke="#a6b9b0" />
        {rows.map((r, i) => (
          <circle
            key={i}
            cx={
              35 +
              ((timeAxis ? r[x] - minx : Math.log1p(Math.abs(r[x]))) / maxx) *
                505
            }
            cy={200 - (Math.log1p(Math.abs(r[y])) / maxy) * 180}
            r="3"
            fill="#248464"
            opacity=".5"
          >
            <title>{`${x}: ${r[x]}, ${y}: ${r[y]}`}</title>
          </circle>
        ))}
        <text x="240" y="225">
          {timeAxis ? "Posting time (UTC; chronological)" : x + " (log scale)"}
        </text>
      </svg>
      <small>
        {timeAxis
          ? `${new Date(minx * 1000).toISOString().slice(0, 10)} to ${new Date((minx + maxx) * 1000).toISOString().slice(0, 10)} · `
          : ""}
        {rows.length} displayed points. Full outputs saved in artifacts.
      </small>
    </section>
  );
}
function Table({
  rows,
  columns,
}: {
  rows: Data[];
  columns: [string, string][];
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map(([key, name]) => (
              <th key={key}>{name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map(([key]) => (
                <td key={key}>
                  {typeof r[key] === "number"
                    ? key === "r2"
                      ? r[key].toFixed(3)
                      : num(r[key])
                    : String(r[key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p>No records available.</p>}
    </div>
  );
}
export default function App() {
  const request = useRef(0);
  const [loadedPage, setLoadedPage] = useState("");
  const [page, setPage] = useState("Overview"),
    [status, setStatus] = useState<Data | null>(null),
    [data, setData] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false);
  const [participant, setParticipant] = useState("1"),
    [offset, setOffset] = useState(0),
    [clock, setClock] = useState(0),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(60);
  const [prediction, setPrediction] = useState<Data | null>(null),
    [context, setContext] = useState<Data>({
      participant: "new-user",
      source: "com.example.mail",
      posted_at: 1528232400,
      priority: 0,
      ringer: 2,
      idle: 0,
      interactive: 1,
      screen_state: 2,
    });
  const [prefs, setPrefs] = useState<Data>({
    protected_sources: ["demo.emergency"],
    digest_interval_seconds: 300,
    maximum_delay_seconds: 120,
  });
  const [newItem, setNewItem] = useState({
    key: "synthetic:custom-1",
    source: "demo.social",
    title: "Synthetic local notification",
  });
  const [experiment, setExperiment] = useState("A");
  const activePage = useRef(page);
  activePage.current = page;
  async function refresh() {
    const id = ++request.current;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const s = await api("status");
      if (id !== request.current) return;
      setStatus(s);
      const path = (
        {
          "Dataset audit": "audit",
          "Exploratory analysis": "analysis",
          "Model comparison": "evaluation",
          "Historical replay": `replay?participant=${encodeURIComponent(participant)}&offset=${offset}`,
          "Load analysis": `load?participant=${encodeURIComponent(participant)}`,
          "Management simulator": "simulator",
          Preferences: "preferences",
          "Model card": "model-card",
        } as Record<string, string>
      )[page];
      const d = path ? await api(path) : s;
      if (id !== request.current) return;
      setData(d);
      setLoadedPage(page);
      if (page === "Preferences") setPrefs(d);
      if (page === "Historical replay" && d.items?.length) {
        setClock(d.items[0].posted_at);
        setPlaying(false);
      }
    } catch (e) {
      if (id === request.current) {
        setError(String(e));
        setLoadedPage(page);
      }
    } finally {
      if (id === request.current) setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
  }, [page, participant, offset]);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setClock((t) => t + speed), 500);
    return () => clearInterval(id);
  }, [playing, speed]);
  async function action(path: string, method = "POST", body?: unknown) {
    const origin = page;
    setBusy(true);
    setError("");
    try {
      const d = await api(path, method, body);
      if (activePage.current === origin) setData(d);
    } catch (e) {
      if (activePage.current === origin) setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  const ev = status?.evaluation?.experiments;
  const selected = ev?.B?.comparisons?.find(
    (r: Data) => r.model === ev.B.selected,
  );
  const audit = status?.audit;
  const replay = data?.items?.filter((r: Data) => r.posted_at <= clock) || [];
  return (
    <div className="shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside>
        <div className="brand">
          <span className="brand-icon">N</span>
          <div>
            Notification Lab<small>AI / ML MINI PROJECT</small>
          </div>
        </div>
        <nav aria-label="Main navigation">
          {pages.map((p, i) => (
            <button
              key={p}
              aria-current={page === p ? "page" : undefined}
              className={page === p ? "active" : ""}
              onClick={() => {
                setPlaying(false);
                setPage(p);
                setError("");
              }}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              {p}
            </button>
          ))}
        </nav>
        <div className="aside-note">
          Study the signal.
          <br />
          Respect its limits.<small>Removal is not evidence of reading.</small>
        </div>
      </aside>
      <main id="main">
        <header>
          <span>RESEARCH WORKSPACE</span>
          <Badge>
            {status?.model_status === "trained"
              ? "Local model · trained"
              : "Model · " + (status?.model_status || "loading")}
          </Badge>
        </header>
        <div className="heading">
          <div>
            <p className="eyebrow">NOTIFICATION OVERLOAD ANALYSIS</p>
            <h1>{page}</h1>
            <p>
              {page === "Overview"
                ? "Understand notification patterns and estimate recorded removal time."
                : "Real evidence, visible assumptions, reproducible results."}
            </p>
          </div>
          <button
            className="secondary"
            onClick={() => void refresh()}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}
        {loading || loadedPage !== page ? (
          <div className="panel" role="status">
            Loading local research data…
          </div>
        ) : !data ? (
          <div className="panel">
            Data unavailable. Start the backend and retry.
          </div>
        ) : (
          <>
            {page === "Overview" && (
              <>
                <div className="hero">
                  <div>
                    <Badge>REAL DATASET · OBSERVED EPISODES</Badge>
                    <h2>
                      From notification overload
                      <br />
                      to measurable patterns.
                    </h2>
                    <p>
                      Analyze recorded delivery and removal events, compare
                      held-out regressors, and explore grouping policies inside
                      a local simulator.
                    </p>
                    <button onClick={() => setPage("Historical replay")}>
                      Open historical replay ↗
                    </button>
                  </div>
                  <div className="hero-mark" aria-hidden="true">
                    <span>POSTED</span>
                    <div>→</div>
                    <span>REMOVED</span>
                    <small>Recorded elapsed time</small>
                  </div>
                </div>
                <div className="stats">
                  <Stat
                    label="Logged records"
                    value={num(audit?.raw_rows)}
                    detail="Unchanged upstream SQL archive"
                  />
                  <Stat
                    label="Usable episodes"
                    value={num(audit?.usable_samples)}
                    detail="Conservative observed-duration sample"
                  />
                  <Stat
                    label="Participants"
                    value={num(
                      audit?.distinct_participant_traces ?? audit?.participants,
                    )}
                    detail="Distinct traces · duplicate ID 7 excluded"
                  />
                  <Stat
                    label="Held-out mean user MAE"
                    value={formatSeconds(
                      selected?.held_out.participant_average_mae_seconds,
                    )}
                    detail="Experiment B · balanced across users"
                  />
                </div>
                <div className="grid">
                  <section className="panel">
                    <h3>Research status</h3>
                    <dl>
                      <dt>Dataset</dt>
                      <dd>{status?.dataset}</dd>
                      <dt>Model</dt>
                      <dd>{status?.model?.model || status?.model_reason}</dd>
                      <dt>Selection criterion</dt>
                      <dd>Development participant-average MAE</dd>
                      <dt>Test evidence</dt>
                      <dd>A: unseen users · B: future notifications</dd>
                    </dl>
                    <button onClick={() => setPage("Model comparison")}>
                      Inspect actual evaluation
                    </button>
                  </section>
                  <section className="panel">
                    <h3>Interpret with care</h3>
                    <p>
                      Removal does not prove reading, attention or importance.
                      Unusual notification load does not prove fatigue.
                    </p>
                    <p>
                      A long predicted removal time is not grounds to suppress
                      an item. This site manages only its own simulator queues.
                    </p>
                    <button
                      className="secondary"
                      onClick={() => setPage("Model card")}
                    >
                      Read model limitations
                    </button>
                  </section>
                </div>
              </>
            )}
            {page === "Dataset audit" && (
              <>
                <div className="stats">
                  <Stat
                    label="Raw rows"
                    value={num(data.raw_rows)}
                    detail="Parsed SQL values; dump never executed"
                  />
                  <Stat
                    label="Unknown removal records"
                    value={num(data.zero_removal_records)}
                    detail="Not zero duration or assumed censoring"
                  />
                  <Stat
                    label="Usable episodes"
                    value={num(data.usable_samples)}
                    detail="Full raw serial lineage preserved"
                  />
                </div>
                <section className="panel">
                  <h3>Provenance</h3>
                  <a href={data.source} target="_blank" rel="noreferrer">
                    Upstream dataset repository ↗
                  </a>
                  <p>{data.citation}</p>
                  <dl>
                    <dt>Retrieved</dt>
                    <dd>{data.retrieval_date}</dd>
                    <dt>SHA-256</dt>
                    <dd className="hash">{data.sha256}</dd>
                    <dt>Usage</dt>
                    <dd>{data.usage_terms}</dd>
                    <dt>Timestamps</dt>
                    <dd>{data.timestamp_units}</dd>
                    <dt>Follow-up</dt>
                    <dd>{data.followup}</dd>
                  </dl>
                </section>
                <div className="grid">
                  <Bars
                    rows={Object.entries(data.exclusions || {}).map(
                      ([reason, count]) => ({ reason, count }),
                    )}
                    label="reason"
                    value="count"
                    title="Episode disposition"
                  />
                  <section className="panel">
                    <h3>Schema and missingness</h3>
                    <Table
                      rows={Object.entries(data.types || {}).map(
                        ([field, type]) => ({
                          field,
                          type,
                          missing: data.missingness[field],
                        }),
                      )}
                      columns={[
                        ["field", "Field"],
                        ["type", "Parsed type"],
                        ["missing", "Null count"],
                      ]}
                    />
                    <p>
                      Zero timestamps are sentinels; null counts alone do not
                      describe missing outcomes.
                    </p>
                  </section>
                </div>
                <details className="panel">
                  <summary>Actual SQL schema</summary>
                  <pre>{data.schema}</pre>
                </details>
              </>
            )}
            {page === "Exploratory analysis" && (
              <>
                <Badge>{data.status}</Badge>
                <div className="grid">
                  <Bars
                    rows={data.duration}
                    label="range"
                    value="count"
                    title="Observed duration distribution"
                  />
                  <Bars
                    rows={data.sources}
                    label="source"
                    value="count"
                    title="Sources · usable episode counts"
                  />
                  <Bars
                    rows={data.participants}
                    label="participant"
                    value="median_seconds"
                    title="Participant median removal · seconds"
                  />
                  <Plot
                    rows={data.load}
                    x="time"
                    y="count"
                    title="Canonical postings per 15-minute UTC window"
                  />
                </div>
                <section className="panel">
                  <h3>Source details</h3>
                  <Table
                    rows={data.sources}
                    columns={[
                      ["source", "Source"],
                      ["count", "Samples"],
                      ["median_seconds", "Median seconds"],
                    ]}
                  />
                </section>
              </>
            )}
            {page === "Model comparison" && (
              <>
                <div className="toolbar">
                  <label>
                    Experiment
                    <select
                      value={experiment}
                      onChange={(e) => setExperiment(e.target.value)}
                    >
                      <option value="A">A · Unseen participants</option>
                      <option value="B">
                        B · Future notifications for known users
                      </option>
                    </select>
                  </label>
                  <Badge>HELD-OUT REAL EVALUATION</Badge>
                </div>
                {data.experiments?.[experiment] ? (
                  (() => {
                    const e = data.experiments[experiment];
                    return (
                      <>
                        <div className="stats">
                          <Stat
                            label="Selected on development"
                            value={e.selected}
                            detail="Participant-average MAE; test excluded"
                          />
                          <Stat
                            label="Training episodes"
                            value={num(e.train_samples)}
                            detail="Observable training labels only"
                          />
                          <Stat
                            label="Final test episodes"
                            value={num(e.test_samples)}
                            detail={`${e.test_participants} test participants`}
                          />
                        </div>
                        <section className="panel">
                          <h3>Baseline and model results · original seconds</h3>
                          <Table
                            rows={e.comparisons.map((r: Data) => ({
                              model: r.model,
                              dev: r.development_participant_mae,
                              ...r.held_out,
                            }))}
                            columns={[
                              ["model", "Model"],
                              ["dev", "Dev mean user MAE"],
                              [
                                "participant_average_mae_seconds",
                                "Test mean user MAE",
                              ],
                              ["mae_seconds", "Pooled MAE"],
                              ["median_absolute_error_seconds", "Median AE"],
                              ["rmse_seconds", "RMSE"],
                              ["r2", "R²"],
                            ]}
                          />
                          <p>
                            Long valid durations are retained. R² is
                            supplementary. A baseline may win.
                          </p>
                        </section>
                        <div className="grid">
                          <Bars
                            rows={e.ablations}
                            label="features"
                            value="development_participant_mae"
                            title="Ablation · fixed gradient booster development fold-average user MAE"
                          />
                          <Plot
                            rows={e.plot_sample}
                            x="actual"
                            y="predicted"
                            title="Prediction versus observed seconds"
                          />
                          <Plot
                            rows={e.plot_sample.map((r: Data) => ({
                              ...r,
                              absolute_residual: Math.abs(
                                r.actual - r.predicted,
                              ),
                            }))}
                            x="predicted"
                            y="absolute_residual"
                            title="Absolute residual versus prediction"
                          />
                          <section className="panel">
                            <h3>Selected model · error groups</h3>
                            <Table
                              rows={Object.entries(e.diagnostics.subgroups).map(
                                ([group, v]) => ({ group, ...(v as Data) }),
                              )}
                              columns={[
                                ["group", "Group"],
                                ["n", "Samples"],
                                ["mae_seconds", "MAE seconds"],
                              ]}
                            />
                          </section>
                        </div>
                        <section className="panel">
                          <h3>Per-participant test error · selected model</h3>
                          <Bars
                            rows={Object.entries(
                              e.comparisons.find(
                                (r: Data) => r.model === e.selected,
                              ).held_out.per_participant_mae_seconds,
                            ).map(([participant, mae]) => ({
                              participant,
                              mae,
                            }))}
                            label="participant"
                            value="mae"
                            title="MAE seconds"
                          />
                        </section>
                      </>
                    );
                  })()
                ) : (
                  <p>No evaluation exists. Run the real-data pipeline.</p>
                )}
              </>
            )}
            {page === "Prediction" && (
              <div className="grid">
                <form
                  className="panel"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    setBusy(true);
                    setError("");
                    try {
                      setPrediction(await api("predict", "POST", context));
                    } catch (err) {
                      setError(String(err));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  <h3>Posting-time context</h3>
                  <p>
                    Unix seconds. Earlier dataset history is used for a matching
                    participant; new users receive explicit fallbacks.
                  </p>
                  {["participant", "source", "posted_at"].map((k) => (
                    <label key={k}>
                      {k.replace("_", " ")}
                      <input
                        required
                        type={k === "posted_at" ? "number" : "text"}
                        min={k === "posted_at" ? 1 : undefined}
                        value={context[k]}
                        onChange={(e) =>
                          setContext({
                            ...context,
                            [k]:
                              k === "posted_at"
                                ? Number(e.target.value)
                                : e.target.value,
                          })
                        }
                      />
                    </label>
                  ))}
                  {[
                    ["priority", [-2, -1, 0, 1, 2]],
                    ["ringer", [0, 1, 2]],
                    ["idle", [0, 1]],
                    ["interactive", [0, 1]],
                    ["screen_state", [0, 1, 2, 3, 4]],
                  ].map(([k, values]) => (
                    <label key={String(k)}>
                      {String(k).replace("_", " ")}
                      <select
                        value={context[String(k)] ?? ""}
                        onChange={(e) =>
                          setContext({
                            ...context,
                            [String(k)]:
                              e.target.value === ""
                                ? null
                                : Number(e.target.value),
                          })
                        }
                      >
                        <option value="">Missing</option>
                        {(values as number[]).map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                  ))}
                  <button disabled={busy}>
                    {busy ? "Predicting…" : "Predict recorded removal duration"}
                  </button>
                </form>
                <section className="panel result">
                  <h3>Removal-duration estimate</h3>
                  {prediction ? (
                    <>
                      <Badge>{prediction.model_status}</Badge>
                      <strong>
                        {formatSeconds(prediction.predicted_duration)}
                      </strong>
                      <p>
                        Version: {prediction.model_version || "Unavailable"}
                      </p>
                      {prediction.fallback_information.map((s: string) => (
                        <p key={s}>{s}</p>
                      ))}
                      {prediction.load && (
                        <p>
                          Previous 15-minute load: {prediction.load.current}.
                          Reference {num(prediction.load.reference)}; threshold{" "}
                          {num(prediction.load.threshold)}.{" "}
                          {prediction.load.unusual
                            ? "Unusual notification load"
                            : "Within reference threshold"}
                          .
                        </p>
                      )}
                    </>
                  ) : (
                    <p>
                      Enter posting-time context to request a local model
                      estimate.
                    </p>
                  )}
                  <div className="note">
                    An estimate of recorded elapsed time. It is not a confidence
                    percentage or a measure of importance.
                  </div>
                </section>
              </div>
            )}
            {page === "Historical replay" && (
              <>
                <div className="toolbar">
                  <label>
                    Participant
                    <select
                      value={participant}
                      onChange={(e) => {
                        setParticipant(e.target.value);
                        setOffset(0);
                      }}
                    >
                      {(audit?.endpoints || [])
                        .filter(
                          (u: Data) =>
                            !audit?.duplicate_participant_traces?.[
                              u.participant
                            ],
                        )
                        .map((u: Data) => (
                          <option key={u.participant} value={u.participant}>
                            {u.participant}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    Virtual seconds per tick
                    <input
                      type="number"
                      value={speed}
                      min="1"
                      onChange={(e) =>
                        setSpeed(Math.max(1, Number(e.target.value)))
                      }
                    />
                  </label>
                  <button onClick={() => setPlaying(!playing)}>
                    {playing ? "Pause" : "Play"}
                  </button>
                  <button
                    onClick={() =>
                      setClock(
                        data.items?.[
                          Math.min(replay.length, (data.items?.length || 1) - 1)
                        ]?.posted_at || clock,
                      )
                    }
                  >
                    Next event
                  </button>
                  <button
                    className="secondary"
                    onClick={() => {
                      setPlaying(false);
                      setClock(data.items?.[0]?.posted_at || 0);
                    }}
                  >
                    Restart page
                  </button>
                </div>
                <section className="panel">
                  <Badge>REAL HISTORICAL EVENTS · VIRTUAL CLOCK</Badge>
                  <h3>
                    {new Date(clock * 1000).toISOString()} · {replay.length}{" "}
                    visible
                  </h3>
                  <p>
                    {data.history_mode}. Observed outcomes stay separate from
                    simulated delivery.
                  </p>
                  <div className="replay-list">
                    {replay.map((r: Data) => (
                      <article key={r.episode_id}>
                        <div>
                          <b>{r.source}</b>
                          <small>
                            {new Date(r.posted_at * 1000).toISOString()} ·{" "}
                            {r.episode_id}
                          </small>
                          <small>
                            Observed:{" "}
                            {formatSeconds(r.observed_duration_seconds)} ·{" "}
                            {r.episode_status}
                          </small>
                        </div>
                        <div>
                          <b>
                            {formatSeconds(r.prediction.predicted_duration)}
                          </b>
                          <small>Predicted removal</small>
                          <Badge>
                            {r.prediction.load?.unusual
                              ? "Unusual load"
                              : `Load ${r.prediction.load?.current ?? "unavailable"}`}
                          </Badge>
                          <button
                            className="secondary"
                            disabled={busy}
                            onClick={async () => {
                              setBusy(true);
                              try {
                                await api("simulator/ingest", "POST", {
                                  key: "historical:" + r.episode_id,
                                  source: r.source,
                                  title:
                                    "Historical policy replay " + r.episode_id,
                                  posted_at: r.posted_at,
                                  mode: "historical",
                                });
                                setError("");
                              } catch (e) {
                                setError(String(e));
                              } finally {
                                setBusy(false);
                              }
                            }}
                          >
                            Add to policy simulator
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                  <div className="toolbar">
                    <button
                      disabled={!offset}
                      onClick={() => setOffset(Math.max(0, offset - 50))}
                    >
                      Previous page
                    </button>
                    <span>
                      {offset + 1}–{Math.min(offset + 50, data.total)} /{" "}
                      {data.total}
                    </span>
                    <button
                      disabled={offset + 50 >= data.total}
                      onClick={() => setOffset(offset + 50)}
                    >
                      Next page
                    </button>
                  </div>
                </section>
              </>
            )}
            {page === "Load analysis" && (
              <>
                <div className="toolbar">
                  <label>
                    Participant
                    <select
                      value={participant}
                      onChange={(e) => setParticipant(e.target.value)}
                    >
                      {(audit?.endpoints || [])
                        .filter(
                          (u: Data) =>
                            !audit?.duplicate_participant_traces?.[
                              u.participant
                            ],
                        )
                        .map((u: Data) => (
                          <option key={u.participant} value={u.participant}>
                            {u.participant}
                          </option>
                        ))}
                    </select>
                  </label>
                  <Badge>UNUSUAL LOAD ≠ FATIGUE</Badge>
                </div>
                <div className="stats">
                  <Stat
                    label="Reference count"
                    value={num(data.reference?.reference)}
                    detail="B training-period mean preceding load"
                  />
                  <Stat
                    label="Threshold"
                    value={num(data.reference?.threshold)}
                    detail="B training 95th percentile · strict exceedance"
                  />
                  <Stat
                    label="Unusual posting cutoffs"
                    value={num(data.unusual_count)}
                    detail="No real anomaly labels or accuracy claim"
                  />
                </div>
                <Plot
                  rows={(data.points || []).filter(
                    (_: Data, i: number) =>
                      i %
                        Math.max(
                          1,
                          Math.floor((data.points?.length || 0) / 500),
                        ) ===
                      0,
                  )}
                  x="time"
                  y="current"
                  title="Previous 15-minute canonical posting load"
                />
                <section className="panel">
                  <h3>Unusual periods · first 100 posting cutoffs</h3>
                  <Table
                    rows={(data.points || [])
                      .filter((p: Data) => p.unusual)
                      .slice(0, 100)
                      .map((p: Data) => ({
                        ...p,
                        time: new Date(p.time * 1000).toISOString(),
                      }))}
                    columns={[
                      ["time", "Posting cutoff (UTC)"],
                      ["current", "Current load"],
                      ["reference", "Historical reference"],
                      ["threshold", "Threshold"],
                    ]}
                  />
                  <p>
                    {data.status}. This descriptive reference has no anomaly
                    accuracy estimate.
                  </p>
                </section>
              </>
            )}
            {page === "Management simulator" && (
              <>
                <div className="toolbar">
                  <Badge>LOCAL SIMULATION · PERSISTENT SQLITE</Badge>
                  <button
                    disabled={busy}
                    onClick={() => void action("simulator/seed")}
                  >
                    Reset + seed synthetic demo
                  </button>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => void action("simulator/reset")}
                  >
                    Reset queue
                  </button>
                </div>
                <div className="stats">
                  <Stat
                    label="Virtual clock"
                    value={`${num(data.clock)} sec`}
                    detail="Monotonic; scheduled times survive restart"
                  />
                  <Stat
                    label="Simulated alerts"
                    value={num(data.alerts)}
                    detail="Each digest counts as one alert"
                  />
                  <Stat
                    label="Delivered items"
                    value={num(data.delivered_items)}
                    detail="Original items remain accessible"
                  />
                  <Stat
                    label="Mean queue delay"
                    value={formatSeconds(data.mean_delay_seconds)}
                    detail="Policy statistic, not a human outcome"
                  />
                </div>
                <div className="toolbar">
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action("simulator/clock", "POST", {
                        time: data.clock + 60,
                      })
                    }
                  >
                    Advance 1 minute
                  </button>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action("simulator/clock", "POST", {
                        time: data.clock + 300,
                      })
                    }
                  >
                    Advance 5 minutes
                  </button>
                </div>
                <form
                  className="panel compact-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void action("simulator/ingest", "POST", {
                      ...newItem,
                      posted_at: data.clock,
                      mode: "synthetic",
                    });
                  }}
                >
                  <h3>Ingest a labeled synthetic item</h3>
                  {Object.entries(newItem).map(([k, v]) => (
                    <label key={k}>
                      {k}
                      <input
                        required
                        value={v}
                        onChange={(e) =>
                          setNewItem({ ...newItem, [k]: e.target.value })
                        }
                      />
                    </label>
                  ))}
                  <button disabled={busy}>Ingest idempotently</button>
                </form>
                <div className="grid">
                  <section className="panel">
                    <h3>Deferred queue</h3>
                    {(data.items || [])
                      .filter((r: Data) => r.delivered_at === null)
                      .map((r: Data) => (
                        <article className="queue-item" key={r.key}>
                          <Badge>{r.mode}</Badge>
                          <b>{r.title}</b>
                          <small>
                            {r.source} · digest {r.due}s · deadline {r.deadline}
                            s
                          </small>
                          <button
                            disabled={busy || r.posted_at > data.clock}
                            onClick={() =>
                              void action(
                                `simulator/deliver/${encodeURIComponent(r.key)}`,
                              )
                            }
                          >
                            Deliver now
                          </button>
                        </article>
                      ))}
                  </section>
                  <section className="panel">
                    <h3>Inbox · delivery status</h3>
                    {(data.items || [])
                      .filter((r: Data) => r.delivered_at !== null && !r.digest)
                      .map((r: Data) => (
                        <article className="queue-item" key={r.key}>
                          <Badge>
                            {r.mode} · {r.status}
                          </Badge>
                          <b>{r.title}</b>
                          <small>
                            {r.source} · delivered {r.delivered_at}s · delay{" "}
                            {r.delivered_at - r.posted_at}s
                          </small>
                        </article>
                      ))}
                  </section>
                </div>
                <section className="panel">
                  <h3>Digests · original items</h3>
                  {[
                    ...new Set<string>(
                      (data.items || [])
                        .filter((r: Data) => r.digest)
                        .map((r: Data) => r.digest),
                    ),
                  ].map((id) => (
                    <details key={id} open>
                      <summary>{id}</summary>
                      {data.items
                        .filter((r: Data) => r.digest === id)
                        .map((r: Data) => (
                          <p key={r.key}>
                            {r.title} · {r.source} · {r.mode} · delay{" "}
                            {r.delivered_at - r.posted_at}s
                          </p>
                        ))}
                    </details>
                  ))}
                  <p>
                    Protected sources bypass grouping. Deadlines take precedence
                    when at or before a digest. Predictions never suppress
                    items. Preferences apply at ingestion; queued policy
                    deadlines stay fixed.
                  </p>
                </section>
              </>
            )}
            {page === "Preferences" && (
              <form
                className="panel preference-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void action("preferences", "PUT", prefs);
                }}
              >
                <h3>Grouping policy</h3>
                <label>
                  Protected sources · one per line
                  <textarea
                    value={prefs.protected_sources.join("\n")}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        protected_sources: e.target.value
                          .split("\n")
                          .map((x) => x.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </label>
                <label>
                  Digest interval · seconds
                  <input
                    type="number"
                    min="10"
                    max="86400"
                    required
                    value={prefs.digest_interval_seconds}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        digest_interval_seconds: Number(e.target.value),
                      })
                    }
                  />
                </label>
                <label>
                  Finite maximum delay · seconds
                  <input
                    type="number"
                    min="1"
                    max="86400"
                    required
                    value={prefs.maximum_delay_seconds}
                    onChange={(e) =>
                      setPrefs({
                        ...prefs,
                        maximum_delay_seconds: Number(e.target.value),
                      })
                    }
                  />
                </label>
                <button disabled={busy}>Save persistent preferences</button>
                <p>
                  Delivery occurs at the earlier of deadline or next digest. A
                  deadline wins ties. Saved settings apply to newly ingested
                  items.
                </p>
              </form>
            )}
            {page === "Model card" && (
              <section className="panel">
                <Badge>{data.status}</Badge>
                <h3>Intended use and limits</h3>
                {(
                  data.metadata?.limitations || [
                    "Untrained model. Removal is not reading.",
                  ]
                ).map((s: string) => (
                  <p key={s}>{s}</p>
                ))}
                <details>
                  <summary>Complete local model card</summary>
                  <pre>{data.text}</pre>
                </details>
              </section>
            )}
          </>
        )}
        <footer>
          Undergraduate research prototype · local processing · no external paid
          APIs <span>Removal time ≠ reading time</span>
        </footer>
      </main>
    </div>
  );
}
