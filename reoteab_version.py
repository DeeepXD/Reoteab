VERSION = "1.0.0"
DISPLAY_VERSION = "v1.0.0"
DISPLAY_NAME = f"Reoteab {DISPLAY_VERSION}"
BUILD_CHANNEL = "stable"


def session_diagnostics(config):
    settings = config if isinstance(config, dict) else {}
    route_name = "Non-VIP" if settings.get("non_vip_movement_path", False) else "VIP"
    try:
        playback_multiplier = float(settings.get("fishing_playback_multiplier", 1.0))
    except (TypeError, ValueError):
        playback_multiplier = 1.0
    return (
        f"[Build] {DISPLAY_NAME} ({VERSION}; {BUILD_CHANNEL})",
        f"[Session] Fishing route: {route_name} | playback: {playback_multiplier:.2f}x | "
        f"auto reconnect: {'on' if settings.get('auto_reconnect', False) else 'off'} | "
        f"fishing failsafe rejoin: {'on' if settings.get('fishing_failsafe_rejoin', False) else 'off'}",
    )
