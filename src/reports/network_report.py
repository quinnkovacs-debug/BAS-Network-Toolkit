"""Create readable reports from adapter and discovery information."""

from datetime import datetime

from src.network.adapter_manager import NetworkAdapter
from src.network.discovery_listener import DiscoveryResult


def format_field(label: str, value: object) -> str:
    """Format one report field with consistent spacing."""

    return f"{label + ':':<20}{value}"


def build_network_report(
    adapter: NetworkAdapter,
    discovery_result: DiscoveryResult,
) -> str:
    """Create a plain-text adapter and switch-discovery report."""

    lines: list[str] = [
        "BAS Network Toolkit Report",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "LOCAL ADAPTER",
        "-------------",
        format_field("Adapter", adapter.name),
        format_field("Description", adapter.description),
        format_field("Link status", adapter.status),
        format_field("Link speed", adapter.link_speed),
        format_field("MAC address", adapter.mac_address),
        format_field("Interface index", adapter.interface_index),
        format_field("IPv4 address", adapter.ipv4_address),
        format_field(
            "Prefix length",
            (
                f"/{adapter.prefix_length}"
                if adapter.prefix_length is not None
                else "Not available"
            ),
        ),
        format_field("Subnet mask", adapter.subnet_mask),
        format_field("Default gateway", adapter.gateway),
        format_field("DHCP", adapter.dhcp_display),
        format_field("DNS servers", adapter.dns_display),
        "",
        "SWITCH DISCOVERY",
        "----------------",
        format_field("Protocol", discovery_result.protocol),
    ]

    neighbor = discovery_result.lldp_neighbor

    if neighbor is None:
        lines.extend(
            [
                format_field("Source MAC", discovery_result.source_mac),
                format_field(
                    "Result",
                    "A discovery frame was received but was not parsed.",
                ),
            ]
        )
    else:
        lines.extend(
            [
                format_field("Switch Name", neighbor.system_name),
                format_field("Switch Port", neighbor.port_id),
                format_field(
                    "Port Description",
                    neighbor.port_description,
                ),
                format_field(
                    "Management IP",
                    neighbor.management_address,
                ),
                format_field("Native VLAN", neighbor.vlan_id),
                format_field("Source MAC", neighbor.source_mac),
                format_field("TTL", neighbor.ttl),
                format_field(
                    "System Description",
                    neighbor.system_description,
                ),
            ]
        )

    return "\n".join(lines) + "\n"