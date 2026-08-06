"""Read IPv4-to-MAC mappings from the Windows ARP table."""

import re
import subprocess


MAC_PATTERN = re.compile(
    r"\b([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})\b"
)


def normalize_mac(mac_address: str) -> str:
    """Return a consistently formatted uppercase MAC address."""

    return mac_address.replace(":", "-").upper()


def lookup_mac_address(
    target_ip: str,
    local_interface_ip: str,
) -> str:
    """Return a target's MAC address from the selected adapter's ARP table.

    Args:
        target_ip: IPv4 address of the device.
        local_interface_ip: IPv4 address assigned to the selected adapter.

    Returns:
        A normalized MAC address, or an empty string when unavailable.
    """

    completed = subprocess.run(
        [
            "arp",
            "-a",
            target_ip,
            "-N",
            local_interface_ip,
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )

    if completed.returncode != 0:
        return ""

    for line in completed.stdout.splitlines():
        if target_ip not in line:
            continue

        match = MAC_PATTERN.search(line)

        if match is not None:
            return normalize_mac(match.group(1))

    return ""