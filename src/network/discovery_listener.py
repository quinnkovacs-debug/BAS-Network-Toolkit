"""
Captures LLDP and CDP packets.
"""

from dataclasses import dataclass

from scapy.all import Ether, Packet, sniff

from src.network.capture_interface import normalize_mac
from src.network.lldp_parser import LldpNeighbor, parse_lldp_packet


LLDP_DESTINATION = "01:80:c2:00:00:0e"
CDP_DESTINATION = "01:00:0c:cc:cc:cc"


@dataclass
class DiscoveryResult:
    """Result returned by a discovery capture."""

    protocol: str
    source_mac: str
    destination_mac: str
    ethernet_type: int | None
    lldp_neighbor: LldpNeighbor | None = None


def is_discovery_packet(packet: Packet) -> bool:
    """Return True for LLDP or CDP multicast frames."""

    if not packet.haslayer(Ether):
        return False

    destination = normalize_mac(packet[Ether].dst)

    return destination in {
        LLDP_DESTINATION,
        CDP_DESTINATION,
    }


def identify_protocol(packet: Packet) -> str:
    """Return the discovery protocol represented by a packet."""

    if not packet.haslayer(Ether):
        return "Unknown"

    destination = normalize_mac(packet[Ether].dst)

    if destination == LLDP_DESTINATION:
        return "LLDP"

    if destination == CDP_DESTINATION:
        return "CDP"

    return "Unknown"


def listen_for_discovery(
    capture_interface: str,
    timeout_seconds: int = 60,
) -> DiscoveryResult | None:
    """Wait for one LLDP or CDP packet.

    Args:
        capture_interface: Npcap device path.
        timeout_seconds: Maximum time to listen.

    Returns:
        Parsed discovery result, or ``None`` when the capture times out.
    """

    packets = sniff(
        iface=capture_interface,
        timeout=timeout_seconds,
        count=1,
        lfilter=is_discovery_packet,
        store=True,
    )

    if not packets:
        return None

    packet = packets[0]
    protocol = identify_protocol(packet)

    ethernet_type: int | None = None

    if packet.haslayer(Ether):
        ethernet_type = int(packet[Ether].type)

    result = DiscoveryResult(
        protocol=protocol,
        source_mac=packet[Ether].src,
        destination_mac=packet[Ether].dst,
        ethernet_type=ethernet_type,
    )

    if protocol == "LLDP":
        result.lldp_neighbor = parse_lldp_packet(packet)

    return result