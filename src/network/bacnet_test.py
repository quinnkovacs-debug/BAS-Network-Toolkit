"""Standalone BACnet/IP broadcast discovery test."""

import socket
import time
from src.network.bacnet_probe import is_bacnet_i_am


WHO_IS_BROADCAST = bytes(
    [
        0x81,  # BACnet/IP BVLC
        0x0B,  # Original-Broadcast-NPDU
        0x00,
        0x08,  # BVLC length
        0x01,  # NPDU version
        0x00,  # NPDU control
        0x10,  # Unconfirmed service request
        0x08,  # Who-Is
    ]
)




def main() -> None:
    local_ip = input(
        "Selected adapter IP: "
    ).strip()

    broadcast_ip = input(
        "Subnet broadcast IP: "
    ).strip()

    port = int(
        input("BACnet UDP port: ").strip()
    )

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

        sock.settimeout(0.25)

        print()
        print(
            f"Broadcasting Who-Is on "
            f"{broadcast_ip}:{port}..."
        )

        sock.sendto(
            WHO_IS_BROADCAST,
            (
                broadcast_ip,
                port,
            ),
        )

        deadline = time.monotonic() + 2.0
        devices: set[str] = set()

        while time.monotonic() < deadline:
            try:
                data, source = sock.recvfrom(2048)
            except socket.timeout:
                continue

            source_ip, source_port = source

            print(
                f"UDP packet received from "
                f"{source_ip}:{source_port} "
                f"length={len(data)} "
                f"data={data.hex(' ')}"
            )

            if is_bacnet_i_am(data):
                devices.add(source_ip)

                print(
                    f"*** BACnet I-Am received from "
                    f"{source_ip}:{source_port}"
                )

        print()

        if not devices:
            print("No BACnet I-Am responses detected.")
        else:
            print(
                f"Found {len(devices)} BACnet device(s)."
            )

    finally:
        sock.close()


if __name__ == "__main__":
    main()