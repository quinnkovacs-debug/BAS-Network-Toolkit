"""
Decodes LLDP packets into Python objects.
"""

from dataclasses import dataclass
from ipaddress import ip_address

from scapy.all import Ether, Packet, Raw


@dataclass
class LldpNeighbor:
    """Useful information advertised by an LLDP neighbor."""

    source_mac: str = "Not available"
    chassis_id: str = "Not advertised"
    port_id: str = "Not advertised"
    port_description: str = "Not advertised"
    system_name: str = "Not advertised"
    system_description: str = "Not advertised"
    management_address: str = "Not advertised"
    vlan_id: str = "Not advertised"
    ttl: str = "Not advertised"


def decode_text(value: bytes) -> str:
    """Decode an LLDP text field safely."""

    return value.decode("utf-8", errors="replace").strip()


def parse_management_address(value: bytes) -> str:
    """Parse an LLDP management-address TLV."""

    if len(value) < 2:
        return "Not advertised"

    address_string_length = value[0]

    if address_string_length < 2:
        return "Not advertised"

    address_subtype = value[1]
    address_bytes = value[2 : 1 + address_string_length]

    # LLDP address subtype 1 is IPv4 and subtype 2 is IPv6.
    if address_subtype in (1, 2):
        try:
            return str(ip_address(address_bytes))
        except ValueError:
            pass

    return address_bytes.hex(":") if address_bytes else "Not advertised"


def parse_organizational_tlv(value: bytes, neighbor: LldpNeighbor) -> None:
    """Parse selected organizationally specific LLDP TLVs."""

    if len(value) < 4:
        return

    oui = value[0:3]
    subtype = value[3]
    information = value[4:]

    # IEEE 802.1 OUI: 00-80-C2
    # Subtype 1 is Port VLAN ID.
    if oui == b"\x00\x80\xc2" and subtype == 1 and len(information) >= 2:
        neighbor.vlan_id = str(int.from_bytes(information[:2], byteorder="big"))


def parse_lldp_packet(packet: Packet) -> LldpNeighbor:
    """Extract useful LLDP values from a captured packet."""

    neighbor = LldpNeighbor()

    if packet.haslayer(Ether):
        neighbor.source_mac = packet[Ether].src

    if not packet.haslayer(Raw):
        return neighbor

    data = bytes(packet[Raw].load)
    offset = 0

    while offset + 2 <= len(data):
        header = int.from_bytes(data[offset : offset + 2], byteorder="big")
        offset += 2

        tlv_type = (header >> 9) & 0x7F
        tlv_length = header & 0x1FF

        if offset + tlv_length > len(data):
            break

        value = data[offset : offset + tlv_length]
        offset += tlv_length

        if tlv_type == 0:
            break

        if tlv_type == 1 and len(value) >= 1:
            neighbor.chassis_id = decode_text(value[1:])

        elif tlv_type == 2 and len(value) >= 1:
            neighbor.port_id = decode_text(value[1:])

        elif tlv_type == 3 and len(value) >= 2:
            neighbor.ttl = str(int.from_bytes(value[:2], byteorder="big"))

        elif tlv_type == 4:
            neighbor.port_description = decode_text(value)

        elif tlv_type == 5:
            neighbor.system_name = decode_text(value)

        elif tlv_type == 6:
            neighbor.system_description = decode_text(value)

        elif tlv_type == 8:
            neighbor.management_address = parse_management_address(value)

        elif tlv_type == 127:
            parse_organizational_tlv(value, neighbor)

    return neighbor