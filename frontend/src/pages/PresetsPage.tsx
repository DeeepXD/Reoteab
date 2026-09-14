import { useEffect, useState } from "react";
import { useConfig } from "../contexts/ConfigContext";

type MacroPreset = {
    id: string;
    name: string;
    image_path?: string | null;
};

type PresetState = {
    active_preset_id: string | null;
    presets: MacroPreset[];
};

function imageUrl(path?: string | null) {
    if (!path) return "";
    return `file:///${path.replace(/\\/g, "/")}`;
}

export default function PresetsPage() {
    const { config, setConfig } = useConfig();
    const [presetState, setPresetState] = useState<PresetState>({ active_preset_id: null, presets: [] });
    const [name, setName] = useState("");
    const [imageSource, setImageSource] = useState<string | null>(null);
    const [message, setMessage] = useState("");

    const loadPresets = async () => {
        try {
            const data = await window.pywebview?.api?.get_macro_presets?.();
            if (data && Array.isArray(data.presets)) {
                setPresetState(data);
            }
        } catch (error) {
            setMessage(`Failed to load presets: ${String(error)}`);
        }
    };

    useEffect(() => {
        if (window.pywebview?.api) {
            loadPresets();
            return;
        }
        window.addEventListener("pywebviewready", loadPresets, { once: true });
        return () => window.removeEventListener("pywebviewready", loadPresets);
    }, []);

    const chooseImage = async () => {
        const result = await window.pywebview?.api?.choose_macro_preset_image?.();
        if (result?.success) {
            setImageSource(result.path);
            setMessage("");
        }
    };

    const savePreset = async () => {
        if (!name.trim()) {
            setMessage("Enter a preset name first.");
            return;
        }
        const result = await window.pywebview?.api?.save_macro_preset?.(name.trim(), imageSource);
        if (!result?.success) {
            setMessage(result?.error || "Failed to save preset.");
            return;
        }
        setPresetState(result.presets);
        setName("");
        setImageSource(null);
        setMessage("");
    };

    const loadPreset = async (preset: MacroPreset) => {
        const result = await window.pywebview?.api?.load_macro_preset?.(preset.id);
        if (!result?.success) {
            setMessage(result?.error || "Failed to load preset.");
            return;
        }
        if (result.config) {
            setConfig(result.config);
        }
        setPresetState(result.presets);
        setMessage(`Loaded ${preset.name}.`);
    };

    const removePreset = async (preset: MacroPreset) => {
        if (!window.confirm(`Delete preset \"${preset.name}\"? This cannot be undone.`)) {
            return;
        }
        const result = await window.pywebview?.api?.delete_macro_preset?.(preset.id);
        if (!result?.success) {
            setMessage(result?.error || "Failed to delete preset.");
            return;
        }
        setPresetState(result.presets);
        setMessage("");
    };

    if (!config) return <div style={{ padding: "20px" }}>Loading...</div>;

    return (
        <>
            <div className="page-header">
                <h2>Macro Presets</h2>
                <p>Save and switch fishing, potion crafting, and merchant settings.</p>
            </div>

            <div className="card">
                <div className="card-header">
                    <div>
                        <h3>Save Current Settings</h3>
                        <p>Webhooks, remote control, calibration points, and other general settings are not included.</p>
                    </div>
                </div>

                <div className="preset-create-row">
                    <div className="preset-image-picker">
                        {imageSource ? <img src={imageUrl(imageSource)} alt="Selected preset" /> : <span>Optional image</span>}
                    </div>
                    <input
                        className="form-input"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        placeholder="Preset name"
                        maxLength={80}
                    />
                    <button className="btn" onClick={chooseImage}>Choose Image</button>
                    <button className="btn btn-accent" onClick={savePreset}>Save Preset</button>
                </div>
                {message && <p className="preset-message">{message}</p>}
            </div>

            <div className="card">
                <div className="card-header">
                    <div>
                        <h3>Saved Presets</h3>
                        <p>Loading a preset updates only its saved macro settings.</p>
                    </div>
                </div>

                {presetState.presets.length === 0 ? (
                    <div className="empty-state"><p>No presets saved yet.</p></div>
                ) : (
                    <div className="preset-list">
                        {presetState.presets.map((preset) => {
                            const active = preset.id === presetState.active_preset_id;
                            return (
                                <div key={preset.id} className={`preset-row ${active ? "is-active" : ""}`}>
                                    <div className="preset-thumbnail">
                                        {preset.image_path ? <img src={imageUrl(preset.image_path)} alt="" /> : <span>Preset</span>}
                                    </div>
                                    <div className="preset-name">
                                        <strong>{preset.name}</strong>
                                        {active && <span>Active</span>}
                                    </div>
                                    <button className="btn" onClick={() => loadPreset(preset)}>Load</button>
                                    <button className="btn btn-danger" onClick={() => removePreset(preset)}>Delete</button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </>
    );
}
