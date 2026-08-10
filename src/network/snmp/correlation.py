"""Correlate discovered network devices with managed-switch information."""

from dataclasses import dataclass

from src.network.arp_lookup import normalize_mac
from src.network.snmp.client import SwitchMacEntry
from src.models.network_device import NetworkDevice


@dataclass(slots=True)
class SwitchPortInfo:
    """Switch location associated with one MAC address."""

    switch_name: str
    switch_ip: str
    mac_address: str
    vlan_id: int
    interface_name: str


def build_mac_port_lookup(
    switch_name: str,
    switch_ip: str,
    entries: list[SwitchMacEntry],
) -> dict[str, SwitchPortInfo]:
    """Build a normalized MAC-to-switch-port lookup."""

    lookup: dict[str, SwitchPortInfo] = {}

    for entry in entries:
        mac_address = normalize_mac(entry.mac_address)

        lookup[mac_address] = SwitchPortInfo(
            switch_name=switch_name,
            switch_ip=switch_ip,
            mac_address=mac_address,
            vlan_id=entry.vlan_id,
            interface_name=entry.interface_name,
        )

    return lookup

def enrich_device_with_switch_info(
    device: NetworkDevice,
    lookup: dict[str, SwitchPortInfo],
) -> bool:
    """Add switch information to one discovered network device.

    Returns True when the device MAC was found in the switch lookup.
    """

    if not device.mac_address:
        return False

    try:
        mac_address = normalize_mac(device.mac_address)
    except ValueError:
        return False

    port_info = lookup.get(mac_address)

    if port_info is None:
        return False

    device.switch_name = port_info.switch_name
    device.switch_ip = port_info.switch_ip
    device.switch_port = port_info.interface_name
    device.vlan_id = str(port_info.vlan_id)

    return True