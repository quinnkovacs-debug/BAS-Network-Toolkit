"""Standalone performance test for the subnet scanner."""

import time

from src.network.subnet_scanner import scan_subnet


def show_progress(
    scanned: int,
    total: int,
    found: int,
) -> None:
    """Display scan progress on one terminal line."""

    print(
        f"\rScanned {scanned:>3}/{total} | "
        f"Devices found: {found}",
        end="",
        flush=True,
    )


def main() -> None:
    """Run a test scan of the current local subnet."""

    print("Starting concurrent subnet scan...\n")

    start_time = time.perf_counter()
    discovered_hosts = []

    for host in scan_subnet(
        ipv4_address="172.16.30.231",
        prefix_length=24,
        progress_callback=show_progress,
        max_workers=32,
    ):
        discovered_hosts.append(host)

    elapsed = time.perf_counter() - start_time

    print("\n\nDiscovered hosts")
    print("----------------")

    for host in sorted(
        discovered_hosts,
        key=lambda item: tuple(
            int(part)
            for part in item.ip_address.split(".")
        ),
    ):
        print(host)

    print(f"\nCompleted in {elapsed:.2f} seconds.")
    print(f"Found {len(discovered_hosts)} responsive hosts.")


if __name__ == "__main__":
    main()