"""Concurrent subnet scanning engine."""

from collections.abc import Callable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from ipaddress import IPv4Interface
import socket
import subprocess
import threading


ProgressCallback = Callable[[int, int, int], None]


@dataclass(slots=True)
class SubnetHost:
    """Information about one discovered host."""

    ip_address: str
    ping: bool = False
    http: bool = False
    https: bool = False


def tcp_port_open(
    address: str,
    port: int,
    timeout: float = 0.5,
) -> bool:
    """Return True if a TCP port accepts a connection."""

    try:
        with socket.create_connection(
            (address, port),
            timeout=timeout,
        ):
            return True
    except OSError:
        return False


def ping_host(
    address: str,
    timeout_ms: int = 500,
) -> bool:
    """Return True if the host replies to one Windows ping."""

    completed = subprocess.run(
        [
            "ping",
            "-n",
            "1",
            "-w",
            str(timeout_ms),
            address,
        ],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )

    return completed.returncode == 0


def validate_network(interface: IPv4Interface) -> None:
    """Reject networks larger than /23."""

    if interface.network.prefixlen < 23:
        raise ValueError(
            "Networks larger than /23 are not supported."
        )


def scan_host(address: str) -> SubnetHost:
    """Test one address for ping, HTTP, and HTTPS."""

    return SubnetHost(
        ip_address=address,
        ping=ping_host(address),
        http=tcp_port_open(address, 80),
        https=tcp_port_open(address, 443),
    )


def scan_subnet(
    ipv4_address: str,
    prefix_length: int,
    stop_event: threading.Event | None = None,
    progress_callback: ProgressCallback | None = None,
    max_workers: int = 32,
) -> Iterator[SubnetHost]:
    """Yield responsive hosts from a local IPv4 subnet.

    Args:
        ipv4_address: Address assigned to the selected adapter.
        prefix_length: Adapter IPv4 prefix length.
        stop_event: Optional event used to cancel the scan.
        progress_callback: Optional function receiving
            ``scanned``, ``total``, and ``hosts_found``.
        max_workers: Maximum number of simultaneous host scans.

    Yields:
        Responsive hosts as their scans complete.
    """

    if stop_event is None:
        stop_event = threading.Event()

    if max_workers < 1:
        raise ValueError("max_workers must be at least 1.")

    interface = IPv4Interface(
        f"{ipv4_address}/{prefix_length}"
    )

    validate_network(interface)

    addresses = [
        str(host)
        for host in interface.network.hosts()
    ]

    total_hosts = len(addresses)
    scanned_hosts = 0
    hosts_found = 0

    executor = ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="subnet-scan",
    )

    futures: dict[Future[SubnetHost], str] = {}

    try:
        for address in addresses:
            if stop_event.is_set():
                break

            future = executor.submit(scan_host, address)
            futures[future] = address

        for future in as_completed(futures):
            if stop_event.is_set():
                break

            scanned_hosts += 1

            try:
                result = future.result()
            except Exception:
                # A failure involving one address should not stop
                # the remainder of the subnet scan.
                if progress_callback is not None:
                    progress_callback(
                        scanned_hosts,
                        total_hosts,
                        hosts_found,
                    )
                continue

            if result.ping or result.http or result.https:
                hosts_found += 1
                yield result

            if progress_callback is not None:
                progress_callback(
                    scanned_hosts,
                    total_hosts,
                    hosts_found,
                )

    finally:
        if stop_event.is_set():
            for future in futures:
                future.cancel()

        executor.shutdown(
            wait=True,
            cancel_futures=True,
        )