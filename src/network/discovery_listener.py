"""
Captures LLDP and CDP packets.
"""

from dataclasses import dataclass

from scapy.all import Ether, Packet

from src.network.capture_interface import normalize_mac
from src.network.lldp_parser import LldpNeighbor, parse_lldp_packet
import threading
import time

from scapy.all import AsyncSniffer, Ether, Packet


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
    stop_event: threading.Event | None = None,
) -> DiscoveryResult | None:
    """Wait for one LLDP or CDP packet.

    Args:
        capture_interface: Npcap device path.
        timeout_seconds: Maximum time to listen.
        stop_event: Optional event used to cancel the capture.

    Returns:
        Parsed discovery result, or ``None`` after timeout or cancellation.
    """

    if stop_event is None:
        stop_event = threading.Event()

    captured_packets: list[Packet] = []
    packet_received = threading.Event()

    def handle_packet(packet: Packet) -> None:
        """Store the first discovery packet received."""

        captured_packets.append(packet)
        packet_received.set()

    sniffer = AsyncSniffer(
        iface=capture_interface,
        count=1,
        store=False,
        lfilter=is_discovery_packet,
        prn=handle_packet,
    )

    deadline = time.monotonic() + timeout_seconds

    try:
        sniffer.start()

        while True:
            if packet_received.wait(timeout=0.1):
                break

            if stop_event.is_set():
                break

            if time.monotonic() >= deadline:
                break

    finally:
        if sniffer.running:
            sniffer.stop()

    if not captured_packets:
        return None

    packet = captured_packets[0]
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