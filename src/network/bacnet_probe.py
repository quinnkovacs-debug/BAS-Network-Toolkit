"""Minimal BACnet/IP Who-Is probe for BAS device discovery."""

import socket
import time


BACNET_PORT_START = 47808
BACNET_PORT_END = 47825

# BACnet/IP Original-Broadcast-NPDU
# NPDU: version 1, normal APDU
# APDU: Unconfirmed-Request, Who-Is
WHO_IS_BROADCAST = bytes(
    [
        0x81,  # BACnet/IP BVLC type
        0x0B,  # Original-Broadcast-NPDU
        0x00,
        0x08,  # Total BVLC length = 8
        0x01,  # BACnet NPDU version
        0x00,  # NPDU control
        0x10,  # Unconfirmed service request
        0x08,  # Who-Is
    ]
)




def _bacnet_apdu_offset(data: bytes) -> int | None:
    """Return the APDU offset in a simple BACnet/IP NPDU."""

    if len(data) < 8:
        return None

    if data[0] != 0x81:
        return None

    declared_length = int.from_bytes(
        data[2:4],
        byteorder="big",
    )

    if declared_length > len(data):
        return None

    offset = 4

    # BACnet NPDU version
    if data[offset] != 0x01:
        return None

    offset += 1

    control = data[offset]
    offset += 1

    # Network-layer message rather than an application APDU.
    if control & 0x80:
        return None

    # Destination specifier present.
    if control & 0x20:
        if offset + 3 > len(data):
            return None

        offset += 2
        dlen = data[offset]
        offset += 1

        if offset + dlen + 1 > len(data):
            return None

        offset += dlen
        offset += 1  # Hop count

    # Source specifier present.
    if control & 0x08:
        if offset + 3 > len(data):
            return None

        offset += 2
        slen = data[offset]
        offset += 1

        if offset + slen > len(data):
            return None

        offset += slen

    return offset


def is_bacnet_i_am(data: bytes) -> bool:
    """Return True if the packet contains a BACnet I-Am APDU."""

    offset = _bacnet_apdu_offset(data)

    if offset is None or offset + 2 > len(data):
        return False

    pdu_type = data[offset] & 0xF0
    service_choice = data[offset + 1]

    return (
        pdu_type == 0x10
        and service_choice == 0x00
    )


def probe_bacnet_port(
    target_ip: str,
    port: int,
    local_interface_ip: str,
    timeout: float = 0.5,
) -> bool:
    """Send BACnet Who-Is and detect a valid I-Am response."""

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        sock.bind(
            (
                local_interface_ip,
                0,
            )
        )

        sock.settimeout(timeout)

        sock.sendto(
            WHO_IS_BROADCAST,
            (
                target_ip,
                port,
            ),
        )

        deadline = time.monotonic() + timeout

        while True:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                return False

            sock.settimeout(remaining)

            try:
                data, source = sock.recvfrom(2048)
            except socket.timeout:
                return False

            source_ip, source_port = source

            if source_ip != target_ip:
                continue

            if source_port != port:
                continue

            if is_bacnet_i_am(data):
                return True

    except OSError:
        return False

    finally:
        sock.close()


def probe_bacnet_ports(
    target_ip: str,
    local_interface_ip: str,
    port_start: int = BACNET_PORT_START,
    port_end: int = BACNET_PORT_END,
) -> set[int]:
    """Return BACnet UDP ports that respond with I-Am."""

    responding_ports: set[int] = set()

    for port in range(
        port_start,
        port_end + 1,
    ):
        if probe_bacnet_port(
            target_ip=target_ip,
            port=port,
            local_interface_ip=local_interface_ip,
        ):
            responding_ports.add(port)

    return responding_ports

def discover_bacnet_subnet(
    local_interface_ip: str,
    broadcast_ip: str,
    port_start: int = BACNET_PORT_START,
    port_end: int = BACNET_PORT_END,
    response_window: float = 1.0,
) -> dict[str, set[int]]:
    """Discover BACnet/IP devices across a range of UDP ports."""

    discovered: dict[str, set[int]] = {}

    for port in range(port_start, port_end + 1):
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        try:
            sock.bind(
                (
                    "0.0.0.0",
                    port,
                )
            )

            sock.settimeout(0.1)

            sock.sendto(
                WHO_IS_BROADCAST,
                (
                    broadcast_ip,
                    port,
                ),
            )

            deadline = time.monotonic() + response_window

            while time.monotonic() < deadline:
                try:
                    data, source = sock.recvfrom(2048)
                except socket.timeout:
                    continue

                source_ip, source_port = source

                if source_ip == local_interface_ip:
                    continue

                if not is_bacnet_i_am(data):
                    continue

                discovered.setdefault(
                    source_ip,
                    set(),
                ).add(source_port)

        except OSError:
            continue

        finally:
            sock.close()

    return discovered