"""
Maps Windows network adapters to Npcap interfaces.
"""

from scapy.arch.windows import get_windows_if_list


def normalize_mac(mac_address: str) -> str:
    """Normalize a MAC address for reliable comparison."""

    return mac_address.replace("-", ":").strip().lower()


def find_capture_interface(
    adapter_name: str,
    mac_address: str,
) -> str:
    """Return the Npcap device path matching a Windows adapter.

    Args:
        adapter_name: Friendly Windows adapter name, such as ``Ethernet 4``.
        mac_address: Adapter MAC address.

    Returns:
        Npcap device path suitable for Scapy.

    Raises:
        RuntimeError: If no matching capture interface is found.
    """

    target_mac = normalize_mac(mac_address)

    for interface in get_windows_if_list():
        interface_name = str(interface.get("name") or "")
        interface_mac = normalize_mac(str(interface.get("mac") or ""))
        guid = str(interface.get("guid") or "")

        if (
            interface_name == adapter_name
            and interface_mac == target_mac
            and guid
        ):
            return rf"\Device\NPF_{guid}"

    raise RuntimeError(
        f'No Npcap capture interface matched "{adapter_name}".'
    )