"""Test connectivity and common web ports on one IP address."""

import socket
import subprocess
from dataclasses import dataclass
from ipaddress import ip_address


@dataclass
class TargetProbeResult:
    """Connectivity results for one target."""

    target: str
    ping_reachable: bool
    http_available: bool
    https_available: bool

    @property
    def preferred_url(self) -> str | None:
        """Return the preferred detected web URL."""

        if self.https_available:
            return f"https://{self.target}"

        if self.http_available:
            return f"http://{self.target}"

        return None


def validate_target(target: str) -> str:
    """Validate and normalize an IPv4 or IPv6 address."""

    cleaned_target = target.strip()

    try:
        return str(ip_address(cleaned_target))
    except ValueError as error:
        raise ValueError(
            f'"{cleaned_target}" is not a valid IP address.'
        ) from error


def ping_target(target: str, timeout_ms: int = 1500) -> bool:
    """Return True when Windows receives a ping reply."""

    completed_process = subprocess.run(
        [
            "ping",
            "-n",
            "1",
            "-w",
            str(timeout_ms),
            target,
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )

    return completed_process.returncode == 0


def tcp_port_is_open(
    target: str,
    port: int,
    timeout_seconds: float = 1.5,
) -> bool:
    """Return True when a TCP connection can be established."""

    try:
        with socket.create_connection(
            (target, port),
            timeout=timeout_seconds,
        ):
            return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


def probe_target(target: str) -> TargetProbeResult:
    """Test ping, HTTP, and HTTPS for one IP address."""

    validated_target = validate_target(target)

    return TargetProbeResult(
        target=validated_target,
        ping_reachable=ping_target(validated_target),
        http_available=tcp_port_is_open(validated_target, 80),
        https_available=tcp_port_is_open(validated_target, 443),
    )