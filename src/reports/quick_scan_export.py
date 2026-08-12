"""CSV export for Quick Scan results."""

import csv
from pathlib import Path

from src.models.network_device import NetworkDevice


CSV_HEADERS = [
    "IP Address",
    "MAC Address",
    "Manufacturer",
    "Switch",
    "Switch Management IP",
    "Switch Port",
    "VLAN",
    "Ping",
    "HTTP",
    "HTTPS",
    "FOX",
    "FOXS",
    "Modbus TCP",
    "BACnet UDP Ports",
]


def _yes_no(value: bool) -> str:
    """Return a readable boolean value for CSV output."""

    return "Yes" if value else "No"


def _bacnet_ports(device: NetworkDevice) -> str:
    """Return detected BACnet UDP ports as comma-separated text."""

    ports = sorted(
        int(service.split(":", 1)[1])
        for service in device.udp_services
        if service.startswith("BACnet:")
    )

    return ", ".join(
        str(port)
        for port in ports
    )


def export_quick_scan_csv(
    file_path: str | Path,
    devices: list[NetworkDevice],
) -> None:
    """Write Quick Scan device results to CSV."""

    path = Path(file_path)

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_HEADERS,
        )

        writer.writeheader()

        for device in devices:
            writer.writerow(
                {
                    "IP Address": device.ip_address,
                    "MAC Address": device.mac_address,
                    "Manufacturer": device.vendor,
                    "Switch": device.switch_name,
                    "Switch Management IP": device.switch_ip,
                    "Switch Port": device.switch_port,
                    "VLAN": device.vlan_id,
                    "Ping": _yes_no(device.ping),
                    "HTTP": _yes_no(device.http),
                    "HTTPS": _yes_no(device.https),
                    "FOX": _yes_no(
                        1911 in device.tcp_ports
                    ),
                    "FOXS": _yes_no(
                        4911 in device.tcp_ports
                    ),
                    "Modbus TCP": _yes_no(
                        502 in device.tcp_ports
                    ),
                    "BACnet UDP Ports": _bacnet_ports(
                        device
                    ),
                }
            )