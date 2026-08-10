"""Standalone test of MAC-to-switch correlation."""

from src.models.network_device import NetworkDevice
from src.network.snmp.client import SwitchMacEntry
from src.network.snmp.correlation import (
    build_mac_port_lookup,
    enrich_device_with_switch_info,
)


def main() -> None:
    """Verify lookup creation and NetworkDevice enrichment."""

    entries = [
        SwitchMacEntry(
            mac_address="00-80-F4-12-34-56",
            vlan_id=437,
            bridge_port=11,
            interface_index=11,
            interface_name="Gi3/0/11",
            status="learned",
        )
    ]

    lookup = build_mac_port_lookup(
        switch_name="TEST-SWITCH",
        switch_ip="10.0.0.5",
        entries=entries,
    )

    device = NetworkDevice(
        ip_address="172.16.30.45",
        mac_address="00:80:f4:12:34:56",
        ping=True,
        https=True,
    )

    matched = enrich_device_with_switch_info(
        device=device,
        lookup=lookup,
    )

    print(f"Matched: {matched}")
    print(device)


if __name__ == "__main__":
    main()