from devlab import DevLabDiagnostics


class _Tracker:
    @staticmethod
    def _extract_biome_from_rpc_line(line):
        if '"hoverText":"' not in line:
            return None
        return line.split('"hoverText":"', 1)[1].split('"', 1)[0]


class _Api:
    def __init__(self):
        self._tracker = _Tracker()


def test_replay_uses_only_sanitized_bloxstrap_rpc_lines():
    diagnostics = DevLabDiagnostics(_Api())
    lines = diagnostics._sanitize_replay_lines(
        [
            "ordinary application log",
            '[BloxstrapRPC] {"largeImage":{"hoverText":"CYBERSPACE"}}',
            "another unrelated line",
        ],
        10,
    )

    assert lines == ['[BloxstrapRPC] {"largeImage":{"hoverText":"CYBERSPACE"}}']


def test_replay_generates_a_bounded_default_sequence():
    diagnostics = DevLabDiagnostics(_Api())
    lines = diagnostics._sanitize_replay_lines([], 7)

    assert len(lines) == 7
    assert all("[BloxstrapRPC]" in line for line in lines)
