"""Standalone test for SNMP MAC-to-port correlation."""

import asyncio
import getpass

from src.network.snmp.client import (
    SnmpQueryError,
    normalize_mac,
    query_identity,
    query_mac_table,
)


async def run_test() -> None:
    """Query one switch VLAN and optionally filter one MAC."""

    switch_ip = input("Switch IP: ").strip()
    community = getpass.getpass("SNMP community: ")
    vlan_text = input("VLAN ID: ").strip()
    mac_filter = input(
        "MAC filter (optional): "
    ).strip()

    if not switch_ip or not community or not vlan_text:
        print("Switch IP, community and VLAN are required.")
        return

    try:
        vlan_id = int(vlan_text)
    except ValueError:
        print("VLAN must be a number.")
        return

    try:
        identity = await query_identity(
            host=switch_ip,
            community=community,
        )

        entries = await query_mac_table(
            host=switch_ip,
            community=community,
            vlan_id=vlan_id,
        )

    except (SnmpQueryError, ValueError) as error:
        print(f"SNMP query failed: {error}")
        return

    if mac_filter:
        try:
            wanted_mac = normalize_mac(mac_filter)
        except ValueError as error:
            print(f"Invalid MAC filter: {error}")
            return

        entries = [
            entry
            for entry in entries
            if entry.mac_address == wanted_mac
        ]

    print()
    print(f"Switch: {identity.get('sysName', switch_ip)}")
    print(f"VLAN:   {vlan_id}")
    print()

    if not entries:
        print("No matching forwarding entries were returned.")
        return

    for entry in entries:
        print(
            f"{entry.mac_address:<18} "
            f"{entry.interface_name or 'Unknown':<18} "
            f"bridge={entry.bridge_port:<5} "
            f"ifIndex={entry.interface_index} "
            f"status={entry.status}"
        )


if __name__ == "__main__":
    asyncio.run(run_test())