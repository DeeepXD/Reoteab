import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.request import urlopen

import main
from webview.http import start_server


class FrontendLoadingTests(unittest.TestCase):
    def test_local_frontend_uses_a_reloadable_local_url(self):
        with tempfile.TemporaryDirectory() as temporary:
            dist = Path(temporary)
            (dist / "index.html").write_text("<html><body>Reoteab</body></html>", encoding="utf-8")
            with mock.patch.object(main, "_get_frontend_dist_dirs", return_value=[str(dist)]):
                entry = main.get_frontend_entry()

        self.assertEqual(entry, {"url": str(dist / "index.html")})
        self.assertNotIn("html", entry)

    def test_local_frontend_path_is_served_from_pywebviews_loopback_server(self):
        with tempfile.TemporaryDirectory() as temporary:
            dist = Path(temporary)
            (dist / "index.html").write_text("<html><body>Reoteab</body></html>", encoding="utf-8")
            address, _common_path, _server = start_server([str(dist / "index.html")])
            with urlopen(f"{address}index.html", timeout=2) as response:
                body = response.read().decode("utf-8")

        self.assertIn("Reoteab", body)


if __name__ == "__main__":
    unittest.main()
