"""Network reachability.

The point of this module is to let the UI tell three situations apart, because
they need three different messages:

* no link at all      - the CP0 is not associated with any network
* link, no internet   - associated, but nothing routes (captive portal, dead AP)
* online              - the stream really is the broken part

Link state is read from /proc/net/route, which is a cheap local file read. The
internet probe is a TCP connect and therefore runs on a worker thread, so the
render loop is never blocked by it.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import threading
import time

OFFLINE = "offline"
NO_INTERNET = "no-internet"
ONLINE = "online"
UNKNOWN = "unknown"

ROUTE_FILE = "/proc/net/route"

# Cloudflare DNS: a plain TCP connect to :53 is fast and needs no DNS itself,
# which matters because DNS is often the first thing to fail on a dead link.
PROBE_HOST = "1.1.1.1"
PROBE_PORT = 53
PROBE_TIMEOUT = 2.5

RTF_UP = 0x0001


def has_default_route(path: str = ROUTE_FILE) -> bool | None:
    """True/False if we can tell, None on platforms without /proc/net/route."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return None

    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 4:
            continue
        iface, destination, _gateway, flags = fields[0], fields[1], fields[2], fields[3]
        if iface == "lo" or destination != "00000000":
            continue
        try:
            if int(flags, 16) & RTF_UP:
                return True
        except ValueError:
            return True
    return False


def wifi_ssid() -> str:
    """Best-effort SSID lookup; empty string when it cannot be determined."""
    if shutil.which("iwgetid"):
        try:
            result = subprocess.run(
                ["iwgetid", "-r"], capture_output=True, text=True, timeout=2, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    if shutil.which("nmcli"):
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            for line in result.stdout.splitlines():
                if line.startswith("yes:"):
                    return line.split(":", 1)[1].strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return ""


def probe_internet(host: str = PROBE_HOST, port: int = PROBE_PORT, timeout: float = PROBE_TIMEOUT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class NetworkMonitor:
    """Caches connectivity state and refreshes it without blocking the UI."""

    LINK_TTL = 2.0  # local file read; cheap
    OK_TTL = 30.0  # re-probe interval while things are working
    FAIL_TTL = 5.0  # retry sooner while broken, so recovery shows up fast

    def __init__(self, probe=probe_internet, route_file: str = ROUTE_FILE):
        self._probe = probe
        self._route_file = route_file
        self._state = UNKNOWN
        self._link: bool | None = None
        self._link_at = -1e9
        self._probe_at = -1e9
        self._probing = False
        self._ssid = ""
        self._lock = threading.Lock()

    # -- state -------------------------------------------------------------

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def ssid(self) -> str:
        with self._lock:
            return self._ssid

    @property
    def usable(self) -> bool:
        """True unless we positively know the network is unusable.

        UNKNOWN counts as usable on purpose: on a platform we cannot inspect,
        nagging about Wi-Fi would be worse than staying quiet.
        """
        return self.state not in (OFFLINE, NO_INTERNET)

    @property
    def headline(self) -> str:
        state = self.state
        if state == OFFLINE:
            return "NO WI-FI"
        if state == NO_INTERNET:
            return "NO INTERNET"
        return ""

    @property
    def detail(self) -> str:
        state = self.state
        if state == OFFLINE:
            return "Connect to Wi-Fi, then press SPACE"
        if state == NO_INTERNET:
            ssid = self.ssid
            joined = f"On {ssid} but" if ssid else "Connected but"
            return f"{joined} nothing is routing"
        return ""

    # -- refresh -----------------------------------------------------------

    def invalidate(self) -> None:
        """Force the next poll to re-check; call this after a stream fails."""
        with self._lock:
            self._link_at = -1e9
            self._probe_at = -1e9

    def poll(self, now: float | None = None) -> str:
        now = time.monotonic() if now is None else now

        if now - self._link_at >= self.LINK_TTL:
            self._link_at = now
            link = has_default_route(self._route_file)
            with self._lock:
                self._link = link
                if link is False:
                    self._state = OFFLINE
                    self._ssid = ""
            if link:
                ssid = wifi_ssid()
                with self._lock:
                    self._ssid = ssid

        with self._lock:
            link = self._link
            probing = self._probing
            state = self._state
            probe_at = self._probe_at

        if link is False:
            return OFFLINE

        ttl = self.OK_TTL if state == ONLINE else self.FAIL_TTL
        if not probing and now - probe_at >= ttl:
            with self._lock:
                self._probing = True
            threading.Thread(target=self._run_probe, daemon=True).start()

        return self.state

    def _run_probe(self) -> None:
        ok = False
        try:
            ok = bool(self._probe())
        except Exception:  # noqa: BLE001 - a probe must never take the app down
            ok = False
        finally:
            with self._lock:
                self._probe_at = time.monotonic()
                self._probing = False
                if ok:
                    self._state = ONLINE
                elif self._link is False:
                    self._state = OFFLINE
                else:
                    self._state = NO_INTERNET
