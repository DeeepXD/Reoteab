import { useCallback, useEffect, useState } from "react";
import { useConfig } from "../contexts/ConfigContext";
import ToggleSwitch from "../components/ToggleSwitch";

export default function OtherFeaturesPage() {
    const { config, saveConfig, error } = useConfig();
    const [memoryTrimStatus, setMemoryTrimStatus] = useState<any>(null);

    if (error) return <div style={{ padding: "20px", color: "red" }}>Error: {error}</div>;
    if (!config) return <div style={{ padding: "20px" }}>Loading...</div>;

    const updateConfig = (key: string, value: any) => {
        saveConfig({ ...config, [key]: value });
    };

    const refreshMemoryTrimStatus = useCallback(async () => {
        try {
            const status = await window.pywebview?.api?.get_roblox_memory_trim_status?.();
            if (status) setMemoryTrimStatus(status);
        } catch {
            // The status is optional presentation data.
        }
    }, []);

    useEffect(() => {
        refreshMemoryTrimStatus();
        const interval = window.setInterval(refreshMemoryTrimStatus, 15000);
        return () => window.clearInterval(interval);
    }, [refreshMemoryTrimStatus]);

    const requestMemoryTrim = async () => {
        try {
            const status = await window.pywebview?.api?.trim_roblox_memory_now?.();
            if (status) setMemoryTrimStatus(status);
            window.setTimeout(refreshMemoryTrimStatus, 1000);
        } catch {
            setMemoryTrimStatus({ status: "failed", message: "Could not request a Roblox memory trim." });
        }
    };

    const memoryMb = (bytes?: number) => bytes === undefined ? "" : `${Math.round(bytes / (1024 * 1024))} MB`;

    return (
        <>
            <div className="page-header">
                <h2>Other Features</h2>
                <p>Additional macro capabilities and experimental options</p>
            </div>

            <div className="card">
                <div className="card-header">
                    <div className="card-icon">⚡</div>
                    <div>
                        <h3>Rare Biome Actions</h3>
                        <p>Actions to take when a rare biome is detected</p>
                    </div>
                </div>

                <ToggleSwitch
                    label="Enable buff when Glitched/Dreamspace"
                    description="ONLY use this feature when you have your buffs DISABLED while hunting for Glitched/Dreamspace"
                    checked={config.enable_buff_glitched || false}
                    onChange={(val) => updateConfig("enable_buff_glitched", val)}
                />

                <ToggleSwitch
                    label="Reset character when there's a rare biome"
                    description="Reset character to Sol's Main Island during GLITCHED/DREAMSPACE/CYBERSPACE"
                    checked={config.reset_on_rare || false}
                    onChange={(val) => updateConfig("reset_on_rare", val)}
                />

                <ToggleSwitch
                    label="Teleport back to Limbo when rare biome ends"
                    description="Return to limbo automatically when rare biome ended"
                    checked={config.teleport_back_to_limbo || false}
                    onChange={(val) => updateConfig("teleport_back_to_limbo", val)}
                />
            </div>

            <div className="card">
                <div className="card-header">
                    <div className="card-icon">🛠️</div>
                    <div>
                        <h3>System Settings</h3>
                        <p>Application-wide preferences</p>
                    </div>
                </div>

                <div className="setting-row" style={{ padding: '15px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>Open AppData Folder</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Opens the folder where logs, config, and macro data are stored</div>
                    </div>
                    <button 
                        className="btn primary" 
                        onClick={() => window.pywebview?.api?.open_appdata()}
                        style={{ padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', backgroundColor: 'var(--primary)', color: 'white', border: 'none', fontWeight: 600 }}
                    >
                        Open Folder
                    </button>
                </div>

                <ToggleSwitch
                    label="GLITCHED visual effect on macro UI when GLITCHED biome is found (to look cool ofc)"
                    description={<span style={{ color: "red", fontWeight: "bold" }}>ONLY USE THIS IF YOU ARE NON PHOTOSENSITIVE</span>}
                    checked={config.enable_glitch_effect || false}
                    onChange={(val) => updateConfig("enable_glitch_effect", val)}
                />

                <ToggleSwitch
                    label="Anti-AFK"
                    description="Prevents Roblox disconnection even when Roblox isn't focused"
                    checked={config.anti_afk || false}
                    onChange={(val) => updateConfig("anti_afk", val)}
                />

                <div className="setting-row" style={{ padding: '0 20px 20px 20px', display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Usage Duration (minutes):</span>
                    <input 
                        type="number" 
                        className="form-input" 
                        style={{ width: '80px', textAlign: 'center' }}
                        value={config.anti_afk_interval || "5"}
                        min="1"
                        max="20"
                        onChange={(e) => updateConfig("anti_afk_interval", e.target.value)}
                    />
                </div>

                <ToggleSwitch
                    label="Enable Idle Mode"
                    description="Disable all automated actions except biome/aura detection and anti-afk."
                    checked={config.enable_idle_mode || false}
                    onChange={(val) => updateConfig("enable_idle_mode", val)}
                />

                <ToggleSwitch
                    label="Make Roblox instance on fullscreen"
                    description="Automatically fullscreen Roblox window when macro starts"
                    checked={config.auto_roblox_fullscreen || false}
                    onChange={(val) => updateConfig("auto_roblox_fullscreen", val)}
                />

                <ToggleSwitch
                    label="Close Roblox Chat After Reconnect"
                    description="Closes Roblox chat before the post-reconnect Collection cleanup."
                    checked={config.close_chat_after_reconnect || false}
                    onChange={(val) => updateConfig("close_chat_after_reconnect", val)}
                />

                <ToggleSwitch
                    label="Trim Roblox memory during long sessions"
                    description="Lets Windows release reclaimable Roblox memory while the macro is running. It does not close or restart Roblox, but may briefly reload game data."
                    checked={config.roblox_memory_trim_enabled || false}
                    onChange={(val) => updateConfig("roblox_memory_trim_enabled", val)}
                />
                {config.roblox_memory_trim_enabled && (
                    <div className="setting-row" style={{ padding: '0 20px 20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '15px' }}>
                        <label className="form-label" style={{ margin: 0 }}>Trim every</label>
                        <input
                            type="number"
                            className="form-input"
                            style={{ width: '80px', textAlign: 'center' }}
                            value={config.roblox_memory_trim_interval_minutes || "60"}
                            min="15"
                            max="720"
                            onChange={(e) => updateConfig("roblox_memory_trim_interval_minutes", e.target.value)}
                        />
                        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>minutes when Roblox uses at least</span>
                        <input
                            type="number"
                            className="form-input"
                            style={{ width: '90px', textAlign: 'center' }}
                            value={config.roblox_memory_trim_threshold_mb || "2048"}
                            min="512"
                            max="8192"
                            onChange={(e) => updateConfig("roblox_memory_trim_threshold_mb", e.target.value)}
                        />
                        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>MB</span>
                    </div>
                )}
                <div className="setting-row" style={{ padding: '0 20px 20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px' }}>
                    <button className="btn btn-accent" style={{ fontSize: '11px', padding: '6px 12px' }} onClick={requestMemoryTrim}>
                        Trim Roblox Memory Now
                    </button>
                    <span className="form-hint">
                        {memoryTrimStatus?.status === "trimmed"
                            ? `Last trim: ${memoryMb(memoryTrimStatus.before_rss)} → ${memoryMb(memoryTrimStatus.after_rss)} (${memoryMb(memoryTrimStatus.reclaimed_rss)} released)${memoryTrimStatus.follow_up_rss !== undefined ? ` • after 30s: ${memoryMb(memoryTrimStatus.follow_up_rss)}` : ""}`
                            : memoryTrimStatus?.message || "Run the macro first to test Roblox memory trimming."}
                    </span>
                </div>

                <ToggleSwitch
                    label="AZERTY Keyboard Mode (experimental)"
                    description="Enable this if you currently using AZERTY keyboard layout :aga:"
                    checked={config.azerty_mode || false}
                    onChange={(val) => updateConfig("azerty_mode", val)}
                />
                {/*<ToggleSwitch
                    label="Enable Click to Move (experimental)"
                    description="Allow clicking on the map to move your character (experimental feature)"
                    checked={config.enable_click_to_move || false}
                    onChange={(val) => updateConfig("enable_click_to_move", val)}
                />
                {config.enable_click_to_move && (
                    <div className="form-group" style={{ marginTop: "15px", marginLeft: "10px" }}>
                        <label className="form-label">Click to Move Interval (s):</label>
                        <input
                            className="form-input"
                            type="number"
                            min="5"
                            value={config.click_to_move_interval || "13"}
                            onChange={(e) => updateConfig("click_to_move_interval", e.target.value)}
                            style={{ width: "80px" }}
                        />
                    </div>
                )}*/}
            </div>
        </>
    );
}
