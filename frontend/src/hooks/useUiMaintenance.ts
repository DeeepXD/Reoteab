import { useEffect, useRef } from "react";

type UiState = {
    active_page?: string;
    theme?: string;
    scroll_y?: number;
    editing?: boolean;
    dirty?: boolean;
    modal?: boolean;
    calibration?: boolean;
    file_dialog?: boolean;
    saving?: boolean;
    interaction?: boolean;
};

const isEditable = (target: EventTarget | null) => target instanceof HTMLElement &&
    (target.matches("input, textarea, select, [contenteditable='true']") || target.isContentEditable);

const isTransient = (target: EventTarget | null) => target instanceof HTMLElement &&
    Boolean(target.closest("[data-ui-transient='true']"));

export default function useUiMaintenance(activePage: string, theme: string) {
    const state = useRef<UiState>({ active_page: activePage, theme, scroll_y: 0 });
    const lastSent = useRef(0);

    useEffect(() => {
        state.current.active_page = activePage;
        state.current.theme = theme;
        if (window.pywebview?.api?.report_ui_state) {
            void window.pywebview.api.report_ui_state({
                ...state.current,
                scroll_y: document.querySelector<HTMLElement>(".page-content")?.scrollTop || 0,
            }).catch(() => undefined);
        }
    }, [activePage, theme]);

    useEffect(() => {
        let disposed = false;
        const send = (interaction = false, force = false) => {
            const now = Date.now();
            if (!force && now - lastSent.current < 900) return;
            lastSent.current = now;
            const content = document.querySelector<HTMLElement>(".page-content");
            const focused = document.activeElement;
            const modal = Boolean(document.querySelector("[role='dialog'], [aria-modal='true'], .modal, .overlay"));
            const payload = {
                ...state.current,
                scroll_y: content?.scrollTop || 0,
                editing: isEditable(focused),
                modal,
                interaction,
            };
            if (!disposed && window.pywebview?.api?.report_ui_state) {
                void window.pywebview.api.report_ui_state(payload).catch(() => undefined);
            }
        };

        const recordInteraction = (event: Event) => {
            const target = event.target;
            if (!isTransient(target) && (event.type === "input" || event.type === "change") && isEditable(target)) {
                state.current.dirty = true;
            }
            send(true, true);
        };
        const onFocusOut = () => send(false, true);
        const onWindowFocus = () => send(true, true);
        const onScroll = () => send(false);
        const onCommit = () => {
            state.current.dirty = false;
            send(false, true);
        };

        const content = document.querySelector<HTMLElement>(".page-content");
        window.addEventListener("pointerdown", recordInteraction, true);
        window.addEventListener("keydown", recordInteraction, true);
        window.addEventListener("input", recordInteraction, true);
        window.addEventListener("change", recordInteraction, true);
        window.addEventListener("focusout", onFocusOut, true);
        window.addEventListener("focus", onWindowFocus);
        window.addEventListener("blur", onFocusOut);
        window.addEventListener("reoteab:ui-committed", onCommit as EventListener);
        content?.addEventListener("scroll", onScroll, { passive: true });
        send(false, true);

        return () => {
            disposed = true;
            window.removeEventListener("pointerdown", recordInteraction, true);
            window.removeEventListener("keydown", recordInteraction, true);
            window.removeEventListener("input", recordInteraction, true);
            window.removeEventListener("change", recordInteraction, true);
            window.removeEventListener("focusout", onFocusOut, true);
            window.removeEventListener("focus", onWindowFocus);
            window.removeEventListener("reoteab:ui-committed", onCommit as EventListener);
            content?.removeEventListener("scroll", onScroll);
        };
    }, []);
}
