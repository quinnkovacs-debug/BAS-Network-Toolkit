"""Standalone test for LLDP/CDP discovery."""

from src.network.capture_interface import find_capture_interface
from src.network.discovery_listener import listen_for_discovery


TARGET_NAME = "Ethernet 4"
TARGET_MAC = "00:e0:4c:36:06:4e"


def main() -> None:
    """Capture and display one discovery packet."""

    capture_interface = find_capture_interface(
        TARGET_NAME,
        TARGET_MAC,
    )

    print(f"Listening on: {capture_interface}")
    print("Waiting up to 60 seconds for LLDP or CDP...")

    result = listen_for_discovery(
        capture_interface=capture_interface,
        timeout_seconds=60,
    )

    if result is None:
        print("No LLDP or CDP packet received.")
        return

    print()
    print(f"{result.protocol} packet received")
    print(f"Source MAC:      {result.source_mac}")
    print(f"Destination MAC: {result.destination_mac}")

    if result.ethernet_type is not None:
        print(f"EtherType:       0x{result.ethernet_type:04x}")

    if result.lldp_neighbor is None:
        print("No LLDP neighbor data was parsed.")
        return

    neighbor = result.lldp_neighbor

    print()
    print("LLDP Neighbor")
    print("-------------")
    print(f"Switch Name:        {neighbor.system_name}")
    print(f"Port ID:            {neighbor.port_id}")
    print(f"Port Description:   {neighbor.port_description}")
    print(f"Management Address: {neighbor.management_address}")
    print(f"VLAN ID:            {neighbor.vlan_id}")
    print(f"TTL:                {neighbor.ttl}")
    print(f"Source MAC:         {neighbor.source_mac}")
    print(f"Switch Description: {neighbor.system_description}")


if __name__ == "__main__":
    main()