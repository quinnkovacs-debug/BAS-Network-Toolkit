"""Listen for LLDP or CDP frames on one selected adapter."""

from scapy.all import Ether, sniff
from scapy.arch.windows import get_windows_if_list
from lldp_parser import parse_lldp_packet


TARGET_NAME = "Ethernet 4"
TARGET_MAC = "00:e0:4c:36:06:4e"

LLDP_DESTINATION = "01:80:c2:00:00:0e"
CDP_DESTINATION = "01:00:0c:cc:cc:cc"


def normalize_mac(mac_address: str) -> str:
    """Normalize a MAC address for comparison."""

    return mac_address.replace("-", ":").lower()


def find_capture_interface(name: str, mac_address: str) -> str:
    """Return the Npcap device path matching a Windows adapter."""

    target_mac = normalize_mac(mac_address)

    for interface in get_windows_if_list():
        interface_name = str(interface.get("name") or "")
        interface_mac = normalize_mac(str(interface.get("mac") or ""))
        guid = str(interface.get("guid") or "")

        if interface_name == name and interface_mac == target_mac and guid:
            return rf"\Device\NPF_{guid}"

    raise RuntimeError("No matching Npcap capture interface was found.")


def is_discovery_packet(packet) -> bool:
    """Return True when a packet is addressed to LLDP or CDP multicast."""

    if not packet.haslayer(Ether):
        return False

    destination = normalize_mac(packet[Ether].dst)

    return destination in {
        LLDP_DESTINATION,
        CDP_DESTINATION,
    }


def identify_protocol(packet) -> str:
    """Identify whether a captured packet is LLDP or CDP."""

    destination = normalize_mac(packet[Ether].dst)

    if destination == LLDP_DESTINATION:
        return "LLDP"

    if destination == CDP_DESTINATION:
        return "CDP"

    return "Unknown"


def main() -> None:
    """Listen for one LLDP or CDP packet."""

    capture_interface = find_capture_interface(
        TARGET_NAME,
        TARGET_MAC,
    )

    print(f"Listening on: {capture_interface}")
    print("Waiting up to 60 seconds for LLDP or CDP...")

    packets = sniff(
        iface=capture_interface,
        timeout=60,
        count=1,
        lfilter=is_discovery_packet,
        store=True,
    )

    if not packets:
        print("No LLDP or CDP packet received.")
        return

    packet = packets[0]

    print(f"{identify_protocol(packet)} packet received")
    print(f"Source MAC:      {packet[Ether].src}")
    print(f"Destination MAC: {packet[Ether].dst}")
    print(f"EtherType:       0x{packet[Ether].type:04x}")

    neighbor = parse_lldp_packet(packet)

    print()
    print("LLDP Neighbor")
    print("-------------")
    print(f"System name:        {neighbor.system_name}")
    print(f"Port ID:            {neighbor.port_id}")
    print(f"Port description:   {neighbor.port_description}")
    print(f"Management address: {neighbor.management_address}")
    print(f"VLAN ID:            {neighbor.vlan_id}")
    print(f"TTL:                {neighbor.ttl}")
    print(f"Source MAC:         {neighbor.source_mac}")
    print(f"System description: {neighbor.system_description}")


if __name__ == "__main__":
    main()