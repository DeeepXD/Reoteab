from reoteab_version import BUILD_CHANNEL, DISPLAY_NAME, DISPLAY_VERSION, VERSION, session_diagnostics


def test_beta_2_identity_is_consistent():
    assert VERSION == "1.0.0-beta.2"
    assert DISPLAY_VERSION == "1.0 Beta 2"
    assert DISPLAY_NAME == "Reoteab 1.0 Beta 2"
    assert BUILD_CHANNEL == "tester-beta"


def test_session_diagnostics_include_relevant_safe_context_only():
    diagnostics = session_diagnostics({
        "non_vip_movement_path": True,
        "fishing_playback_multiplier": "1.15",
        "auto_reconnect": True,
        "fishing_failsafe_rejoin": False,
        "private_server_link": "https://private.example/link",
        "webhook_url": "https://discord.com/api/webhooks/secret",
    })

    output = "\n".join(diagnostics)
    assert "Reoteab 1.0 Beta 2" in output
    assert "Non-VIP" in output
    assert "1.15x" in output
    assert "auto reconnect: on" in output
    assert "fishing failsafe rejoin: off" in output
    assert "private.example" not in output
    assert "discord.com" not in output
