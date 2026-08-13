"""Connectivity detection and the offline behaviour it drives."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cpzradio import mixer, net, radio  # noqa: E402
from cpzradio.runtime import KeyEvent  # noqa: E402

# Real /proc/net/route content: header, then a default route and a subnet route.
ROUTE_WITH_DEFAULT = """\
Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT
wlan0\t00000000\t0101A8C0\t0003\t0\t0\t600\t00000000\t0\t0\t0
wlan0\t0001A8C0\t00000000\t0001\t0\t0\t600\t00FFFFFF\t0\t0\t0
"""

ROUTE_NO_DEFAULT = """\
Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT
wlan0\t0001A8C0\t00000000\t0001\t0\t0\t600\t00FFFFFF\t0\t0\t0
"""

ROUTE_LOOPBACK_ONLY = """\
Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT
lo\t00000000\t00000000\t0003\t0\t0\t0\t00000000\t0\t0\t0
"""


class TestRouteParsing(unittest.TestCase):
    def _route_file(self, content: str) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".route", delete=False)
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_default_route_detected(self):
        self.assertTrue(net.has_default_route(self._route_file(ROUTE_WITH_DEFAULT)))

    def test_no_default_route(self):
        self.assertFalse(net.has_default_route(self._route_file(ROUTE_NO_DEFAULT)))

    def test_loopback_default_does_not_count(self):
        self.assertFalse(net.has_default_route(self._route_file(ROUTE_LOOPBACK_ONLY)))

    def test_missing_file_is_unknown_not_offline(self):
        # On a platform without /proc we must not claim the user is offline.
        self.assertIsNone(net.has_default_route("/nonexistent/route"))

    def test_garbage_lines_are_skipped(self):
        self.assertFalse(net.has_default_route(self._route_file("header\nshort line\n")))


class TestNetworkMonitor(unittest.TestCase):
    def _monitor(self, route: str | None, probe_ok: bool):
        if route is None:
            path = "/nonexistent/route"
        else:
            handle = tempfile.NamedTemporaryFile("w", suffix=".route", delete=False)
            handle.write(route)
            handle.close()
            self.addCleanup(os.unlink, handle.name)
            path = handle.name
        return net.NetworkMonitor(probe=lambda: probe_ok, route_file=path)

    @staticmethod
    def _settle(monitor, timeout=3.0):
        """Wait for the probe thread to finish."""
        deadline = threading.Event()
        for _ in range(int(timeout * 100)):
            if not monitor._probing:
                return
            deadline.wait(0.01)

    def test_no_link_is_offline_without_probing(self):
        probed = []
        monitor = net.NetworkMonitor(
            probe=lambda: probed.append(1) or True,
            route_file=self._route_path(ROUTE_NO_DEFAULT),
        )
        self.assertEqual(monitor.poll(now=0), net.OFFLINE)
        self.assertFalse(monitor.usable)
        self.assertEqual(monitor.headline, "NO WI-FI")
        self.assertEqual(probed, [], "must not probe the internet with no link")

    def test_link_plus_probe_success_is_online(self):
        monitor = self._monitor(ROUTE_WITH_DEFAULT, probe_ok=True)
        with mock.patch.object(net, "wifi_ssid", return_value="HomeNet"):
            monitor.poll(now=0)
        self._settle(monitor)
        self.assertEqual(monitor.state, net.ONLINE)
        self.assertTrue(monitor.usable)
        self.assertEqual(monitor.headline, "")

    def test_link_but_failed_probe_is_no_internet(self):
        monitor = self._monitor(ROUTE_WITH_DEFAULT, probe_ok=False)
        with mock.patch.object(net, "wifi_ssid", return_value="HomeNet"):
            monitor.poll(now=0)
        self._settle(monitor)
        self.assertEqual(monitor.state, net.NO_INTERNET)
        self.assertFalse(monitor.usable)
        self.assertEqual(monitor.headline, "NO INTERNET")
        self.assertIn("HomeNet", monitor.detail)

    def test_unknown_platform_stays_usable(self):
        monitor = self._monitor(None, probe_ok=True)
        self.assertTrue(monitor.usable)  # before any probe resolves

    def test_probe_exception_does_not_propagate(self):
        def boom():
            raise RuntimeError("probe blew up")

        monitor = net.NetworkMonitor(
            probe=boom, route_file=self._route_path(ROUTE_WITH_DEFAULT)
        )
        with mock.patch.object(net, "wifi_ssid", return_value=""):
            monitor.poll(now=0)
        self._settle(monitor)
        self.assertEqual(monitor.state, net.NO_INTERNET)

    def test_probe_is_rate_limited(self):
        calls = []
        monitor = net.NetworkMonitor(
            probe=lambda: calls.append(1) or True,
            route_file=self._route_path(ROUTE_WITH_DEFAULT),
        )
        with mock.patch.object(net, "wifi_ssid", return_value=""):
            monitor.poll(now=0)
            self._settle(monitor)
            for tick in range(1, 20):  # ~20 frames within the TTL
                monitor.poll(now=tick * 0.05)
            self._settle(monitor)
        self.assertEqual(len(calls), 1, "probe must not run every frame")

    def test_invalidate_forces_recheck(self):
        calls = []
        monitor = net.NetworkMonitor(
            probe=lambda: calls.append(1) or True,
            route_file=self._route_path(ROUTE_WITH_DEFAULT),
        )
        with mock.patch.object(net, "wifi_ssid", return_value=""):
            monitor.poll(now=0)
            self._settle(monitor)
            monitor.invalidate()
            monitor.poll(now=0.1)
            self._settle(monitor)
        self.assertEqual(len(calls), 2)

    def _route_path(self, content: str) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".route", delete=False)
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name


class TestAppOffline(unittest.TestCase):
    """The behaviour the user actually sees when there is no Wi-Fi."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self._saved = {
            k: os.environ.get(k) for k in ("CPZRADIO_CONFIG_DIR", "CPZRADIO_DATA_DIR")
        }
        os.environ["CPZRADIO_CONFIG_DIR"] = str(root / "config")
        os.environ["CPZRADIO_DATA_DIR"] = str(root / "data")

        patcher = mock.patch.object(mixer.AlsaMixer, "available", staticmethod(lambda: False))
        patcher.start()
        self.addCleanup(patcher.stop)

        from test_app import StubPlayer

        self.player = StubPlayer()
        self.app = radio.RadioApp(player=self.player, autoplay=False)
        self.app.net._state = net.OFFLINE

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def test_search_is_refused_immediately(self):
        """Regression: an offline search used to stack ~45s of timeouts."""
        self.app.screen = "search"
        self.app.query = "jazz"
        self.app.start_search()
        self.assertIsNone(self.app.search_job, "no network request should be made")
        self.assertTrue(self.app.notice)

    def test_search_status_explains_the_cause(self):
        status = self.app.search_status()
        self.assertIn("NO WI-FI", status)
        self.assertNotIn("urlopen", status)

    def test_offline_skips_playlist_resolution(self):
        with mock.patch("cpzradio.radio.resolve_stream_url") as resolver:
            self.app.tune(self.app.visible_stations[0])
        resolver.assert_not_called()

    def test_playing_is_still_attempted_offline(self):
        # Local network streams can work with no internet route, so we still
        # hand the URL to mpv rather than refusing outright.
        station = self.app.visible_stations[0]
        self.app.tune(station)
        self.assertEqual(self.player.url, station.url)

    def test_stream_failure_triggers_a_network_recheck(self):
        from cpzradio.player import ERROR

        self.app._last_player_state = "playing"
        self.player.state = ERROR
        with mock.patch.object(self.app.net, "invalidate") as invalidate:
            self.app.update()
        invalidate.assert_called_once()

    def test_offline_screen_renders(self):
        self.app.screen = "now"
        image = self.app.draw()
        self.assertEqual(image.size, (320, 170))
        self.assertTrue(image.getbbox())

    def test_headline_and_detail_are_non_empty(self):
        self.assertTrue(self.app.net.headline)
        self.assertTrue(self.app.net.detail)


if __name__ == "__main__":
    unittest.main()
