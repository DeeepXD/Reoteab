import { useEffect, useState } from "react";

type Snapshot = {
    recording: boolean;
    latest: Record<string, number | string>;
    samples: Array<Record<string, number | string>>;
    bridge: Record<string, number | boolean | string>;
    transition_queue: number;
    worker_health: Record<string, { state?: string }>;
    pipeline: Array<{ timestamp: string; event: string; state: string; detail: string }>;
    webhook_mode: string;
    fault: string | null;
};

const bytes = (value: unknown) => `${((Number(value) || 0) / 1024 / 1024).toFixed(1)} MB`;

function MemoryGraph({ samples }: { samples: Array<Record<string, number | string>> }) {
    const points = samples.slice(-60);
    const max = Math.max(1, ...points.map(sample => Math.max(Number(sample.backend_rss) || 0, Number(sample.webview_rss) || 0)));
    const line = (key: "backend_rss" | "webview_rss") => points.map((sample, index) => {
        const x = points.length < 2 ? 0 : (index / (points.length - 1)) * 100;
        const y = 100 - ((Number(sample[key]) || 0) / max) * 100;
        return `${x},${y}`;
    }).join(" ");
    return <div style={{ marginTop: 14 }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ height: 72, width: "100%", border: "1px solid var(--border)", borderRadius: 4, background: "rgba(255,255,255,0.02)" }}>
            <polyline points={line("backend_rss")} fill="none" stroke="#22c55e" strokeWidth="2" vectorEffect="non-scaling-stroke" />
            <polyline points={line("webview_rss")} fill="none" stroke="#60a5fa" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        </svg>
        <div style={{ display: "flex", gap: 14, marginTop: 4, color: "var(--text-muted)", fontSize: "0.78rem" }}><span style={{ color: "#22c55e" }}>■ Backend</span><span style={{ color: "#60a5fa" }}>■ WebView2</span><span>Last {points.length} samples</span></div>
    </div>;
}

export default function DevLabPage() {
    const [data, setData] = useState<Snapshot | null>(null);
    const [rate, setRate] = useState(20);
    const [busy, setBusy] = useState(false);

    const refresh = async () => {
        if (!window.pywebview?.api?.get_devlab_snapshot) return;
        try {
            setData(await window.pywebview.api.get_devlab_snapshot());
        } catch (error) {
            console.error("Failed to refresh DevLab:", error);
        }
    };

    useEffect(() => {
        refresh();
        const timer = window.setInterval(refresh, 2000);
        return () => window.clearInterval(timer);
    }, []);

    const call = async (method: string, ...args: unknown[]) => {
        if (!window.pywebview?.api?.[method]) return;
        setBusy(true);
        try {
            await window.pywebview.api[method](...args);
            await refresh();
        } finally {
            setBusy(false);
        }
    };

    const latest = data?.latest || {};
    const bridge = data?.bridge || {};
    const workers = Object.entries(data?.worker_health || {});

    return (
        <>
            <div className="page-header">
                <h2>DevLab</h2>
                <p>Offline diagnostics. This build uses separate Reoteab DevLab data and never sends user webhooks.</p>
            </div>

            <div className="card-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(155px, 1fr))" }}>
                <div className="stat-card"><div className="stat-value">{bytes(latest.backend_rss)}</div><div className="stat-label">Backend memory</div></div>
                <div className="stat-card"><div className="stat-value">{bytes(latest.webview_rss)}</div><div className="stat-label">WebView2 memory</div></div>
                <div className="stat-card"><div className="stat-value">{String(latest.threads || 0)}</div><div className="stat-label">Python threads</div></div>
                <div className="stat-card"><div className="stat-value">{data?.transition_queue || 0}</div><div className="stat-label">Transition queue</div></div>
                <div className="stat-card"><div className="stat-value">{String(bridge.pending || 0)}</div><div className="stat-label">Pending UI updates</div></div>
            </div>

            <div className="card">
                <div className="card-header"><div className="card-icon">📈</div><div><h3>Memory profiler</h3><p>Samples backend and WebView2 child processes every two seconds.</p></div></div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button className="primary-button" disabled={busy || !!data?.recording} onClick={() => call("start_devlab_recording")}>Start recording</button>
                    <button className="secondary-button" disabled={busy || !data?.recording} onClick={() => call("stop_devlab_recording")}>Stop recording</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("export_devlab_report")}>Export CSV and report</button>
                </div>
                <MemoryGraph samples={(data?.samples || []) as Array<Record<string, number | string>>} />
            </div>

            <div className="card">
                <div className="card-header"><div className="card-icon">🧪</div><div><h3>Biome simulator</h3><p>Exercises the production transition handler with isolated configuration and mock delivery.</p></div></div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button className="secondary-button" disabled={busy} onClick={() => call("simulate_devlab_biome", "WINDY", "NORMAL")}>NORMAL → WINDY</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("simulate_devlab_biome", "CYBERSPACE", "NORMAL")}>NORMAL → CYBERSPACE</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("simulate_devlab_biome", "NORMAL", "CYBERSPACE")}>CYBERSPACE → NORMAL</button>
                    <select value={data?.webhook_mode || "success"} onChange={(event) => call("set_devlab_webhook_mode", event.target.value)}>
                        <option value="success">Mock webhook: success</option>
                        <option value="timeout">Mock webhook: timeout</option>
                        <option value="failure">Mock webhook: failure</option>
                    </select>
                    <button className="secondary-button" disabled={busy} onClick={() => call("simulate_devlab_screenshot_webhook")}>Mock screenshot + delivery</button>
                </div>
            </div>

            <div className="card">
                <div className="card-header"><div className="card-icon">⚡</div><div><h3>WebView bridge stress</h3><p>Uses the same bounded bridge as runtime status and biome presentation updates.</p></div></div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                    <label>Updates/sec <input type="number" min="1" max="200" value={rate} onChange={(event) => setRate(Number(event.target.value))} style={{ width: 70, marginLeft: 6 }} /></label>
                    <button className="primary-button" disabled={busy} onClick={() => call("start_devlab_stress", rate)}>Start stress</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("stop_devlab_stress")}>Stop stress</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("set_devlab_fault", "bridge-stall")}>Simulate unresponsive UI</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("set_devlab_fault", "drop-ui")}>Drop UI updates</button>
                    <button className="secondary-button" disabled={busy} onClick={() => call("set_devlab_fault", null)}>Clear fault</button>
                </div>
                <p style={{ marginTop: 12, color: "var(--text-muted)", fontSize: "0.85rem" }}>Bridge: {String(bridge.delivered || 0)} delivered, {String(bridge.coalesced || 0)} coalesced, {String(bridge.dropped || 0)} dropped, blocked {String(bridge.blocked_for || 0)}s.</p>
            </div>

            <div className="card">
                <div className="card-header"><div className="card-icon">🔎</div><div><h3>Pipeline inspector</h3><p>Most recent simulated pipeline activity. No Roblox, input, or real Discord webhook is used.</p></div></div>
                <div style={{ maxHeight: 190, overflowY: "auto", fontFamily: "monospace", fontSize: "0.78rem" }}>
                    {data?.pipeline?.length ? data.pipeline.slice().reverse().map((event, index) => <div key={`${event.timestamp}-${index}`} style={{ padding: "4px 0", borderBottom: "1px solid var(--border)" }}><span style={{ color: "var(--text-muted)" }}>{event.timestamp}</span> &nbsp;{event.event} — <strong>{event.state}</strong>{event.detail ? ` (${event.detail})` : ""}</div>) : <div style={{ color: "var(--text-muted)" }}>No simulated events yet.</div>}
                </div>
                {workers.length > 0 && <p style={{ marginTop: 12, color: "var(--text-muted)", fontSize: "0.82rem" }}>Workers: {workers.map(([name, state]) => `${name}: ${state.state || "unknown"}`).join(" · ")}</p>}
            </div>
        </>
    );
}
