"""Standalone BACnet/IP subnet discovery range test."""

from src.network.bacnet_probe import discover_bacnet_subnet


def main() -> None:
    local_ip = input(
        "Selected adapter IP: "
    ).strip()

    broadcast_ip = input(
        "Subnet broadcast IP: "
    ).strip()

    print()
    print("Scanning BACnet UDP 47808-47825...")
    print()

    devices = discover_bacnet_subnet(
        local_interface_ip=local_ip,
        broadcast_ip=broadcast_ip,
    )

    if not devices:
        print("No BACnet devices detected.")
        return

    for ip_address in sorted(
        devices,
        key=lambda value: tuple(
            int(part)
            for part in value.split(".")
        ),
    ):
        ports = ", ".join(
            str(port)
            for port in sorted(devices[ip_address])
        )

        print(
            f"{ip_address:<16} "
            f"UDP {ports}"
        )

    print()
    print(
        f"Found {len(devices)} BACnet device(s)."
    )


if __name__ == "__main__":
    main()