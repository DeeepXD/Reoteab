import { useEffect } from "react";

type UiEvent = {
    event?: string;
    payload?: unknown;
};

export default function useUiEvents(isApiReady: boolean) {
    useEffect(() => {
        if (!isApiReady) return;
        let disposed = false;
        let inFlight = false;

        const deliver = ({ event, payload }: UiEvent) => {
            if (!event) return;
            if (event === "config") (window as any).onConfigUpdated?.();
            if (event === "macro-status") (window as any).onMacroStatus?.(String(payload || ""));
            if (event === "biome") (window as any).onBiomeUpdate?.(String(payload || ""));
            if (event === "shortcut") (window as any).onShortcutEvent?.(String(payload || ""));
            if (event === "fishing-failsafe") (window as any).onFishingFailsafeWarning?.(String(payload || ""));
            if (event === "calibration-result") {
                (window as any).onCalibrationResult?.(payload);
                (window as any).onCalibrationResultMisc?.(payload);
            }
            if (event === "devlab-status") (window as any).onDevLabStatus?.(payload);
        };

        const poll = async () => {
            if (disposed || inFlight || !window.pywebview?.api?.get_ui_events) return;
            inFlight = true;
            try {
                const events = await window.pywebview.api.get_ui_events();
                if (!disposed && Array.isArray(events)) events.forEach(deliver);
            } catch {
                // The next bounded poll will retry after a renderer restart.
            } finally {
                inFlight = false;
            }
        };

        void poll();
        const timer = window.setInterval(poll, 1000);
        return () => {
            disposed = true;
            window.clearInterval(timer);
        };
    }, [isApiReady]);
}
