"""Data model for a device discovered on the network."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class NetworkDevice:
    """Information collected about one network device."""

    ip_address: str

    # Basic connectivity
    ping: bool = False
    http: bool = False
    https: bool = False

    # Device identity
    device_name: str = ""
    mac_address: str = ""
    vendor: str = ""

    # Protocol information
    tcp_ports: set[int] = field(default_factory=set)
    udp_services: set[str] = field(default_factory=set)

    # Managed-switch correlation
    switch_name: str = ""
    switch_ip: str = ""
    switch_port: str = ""
    vlan_id: str = ""

    @property
    def preferred_url(self) -> str | None:
        """Return the preferred detected web-interface URL."""

        if self.https:
            return f"https://{self.ip_address}"

        if self.http:
            return f"http://{self.ip_address}"

        return None

    @property
    def is_bas_device(self) -> bool:
        """Return True when the device shows evidence of a BAS service."""

        has_bacnet = any(
            service.startswith("BACnet:")
            for service in self.udp_services
        )

        return (
            502 in self.tcp_ports
            or 1911 in self.tcp_ports
            or 4911 in self.tcp_ports
            or has_bacnet
        )