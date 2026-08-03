"""Windows network-adapter discovery functions."""

import ipaddress
import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class NetworkAdapter:
    """Information about one Windows network adapter."""

    name: str
    description: str
    interface_index: int
    status: str
    link_speed: str
    mac_address: str

    ipv4_address: str = "Not assigned"
    prefix_length: int | None = None
    subnet_mask: str = "Not available"
    gateway: str = "Not assigned"
    dhcp_enabled: bool | None = None
    dns_servers: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Return the text displayed in the adapter selector."""

        return f"{self.name} — {self.description}"

    @property
    def dhcp_display(self) -> str:
        """Return a readable DHCP status."""

        if self.dhcp_enabled is True:
            return "Enabled"
        if self.dhcp_enabled is False:
            return "Disabled"
        return "Unknown"

    @property
    def dns_display(self) -> str:
        """Return DNS servers as readable text."""

        if not self.dns_servers:
            return "Not assigned"

        return ", ".join(self.dns_servers)


def prefix_to_subnet_mask(prefix_length: int | None) -> str:
    """Convert an IPv4 prefix length, such as 24, to 255.255.255.0."""

    if prefix_length is None:
        return "Not available"

    try:
        network = ipaddress.IPv4Network(f"0.0.0.0/{prefix_length}")
        return str(network.netmask)
    except ValueError:
        return "Not available"


def get_network_adapters() -> list[NetworkAdapter]:
    """Return network adapters and their IPv4 configuration."""

    powershell_command = r"""
        $results = foreach ($adapter in Get-NetAdapter | Sort-Object Name) {
            $ipConfig = Get-NetIPConfiguration `
                -InterfaceIndex $adapter.ifIndex `
                -ErrorAction SilentlyContinue

            $dhcp = Get-NetIPInterface `
                -InterfaceIndex $adapter.ifIndex `
                -AddressFamily IPv4 `
                -ErrorAction SilentlyContinue |
                Select-Object -First 1

            $dns = Get-DnsClientServerAddress `
                -InterfaceIndex $adapter.ifIndex `
                -AddressFamily IPv4 `
                -ErrorAction SilentlyContinue

            [PSCustomObject]@{
                 Name                 = $adapter.Name
                 InterfaceDescription = $adapter.InterfaceDescription
                 ifIndex              = $adapter.ifIndex
                 Status               = $adapter.Status
                 LinkSpeed            = $adapter.LinkSpeed
                 MacAddress           = $adapter.MacAddress
                 IPv4Address          = $ipConfig.IPv4Address.IPAddress |
                                         Select-Object -First 1
                 PrefixLength         = $ipConfig.IPv4Address.PrefixLength |
                                         Select-Object -First 1
                 Gateway              = $ipConfig.IPv4DefaultGateway.NextHop |
                                         Select-Object -First 1
                 Dhcp                 = if ($null -eq $dhcp) {
                                            $null
                                        }
                                        else {
                                            $dhcp.Dhcp.ToString()
                                        }
                 DnsServers           = @($dns.ServerAddresses)
            }
        }

        $results | ConvertTo-Json -Depth 5
    """

    try:
        completed_process = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "Windows could not list network adapters."
        raise RuntimeError(message) from error

    output = completed_process.stdout.strip()

    if not output:
        return []

    try:
        raw_adapters = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Windows returned adapter information in an unexpected format."
        ) from error

    if isinstance(raw_adapters, dict):
        raw_adapters = [raw_adapters]

    adapters: list[NetworkAdapter] = []

    for raw_adapter in raw_adapters:
        prefix_value = raw_adapter.get("PrefixLength")

        try:
            prefix_length = (
                int(prefix_value) if prefix_value is not None else None
            )
        except (TypeError, ValueError):
            prefix_length = None

        dhcp_value = str(raw_adapter.get("Dhcp") or "").lower()

        if dhcp_value == "enabled":
            dhcp_enabled = True
        elif dhcp_value == "disabled":
            dhcp_enabled = False
        else:
            dhcp_enabled = None

        raw_dns = raw_adapter.get("DnsServers") or []

        if isinstance(raw_dns, str):
            dns_servers = [raw_dns]
        else:
            dns_servers = [
                str(server)
                for server in raw_dns
                if server
            ]

        adapters.append(
            NetworkAdapter(
                name=str(raw_adapter.get("Name") or "Unknown"),
                description=str(
                    raw_adapter.get("InterfaceDescription") or "Unknown adapter"
                ),
                interface_index=int(raw_adapter.get("ifIndex") or 0),
                status=str(raw_adapter.get("Status") or "Unknown"),
                link_speed=str(raw_adapter.get("LinkSpeed") or "Unknown"),
                mac_address=str(
                    raw_adapter.get("MacAddress") or "Not available"
                ),
                ipv4_address=str(
                    raw_adapter.get("IPv4Address") or "Not assigned"
                ),
                prefix_length=prefix_length,
                subnet_mask=prefix_to_subnet_mask(prefix_length),
                gateway=str(raw_adapter.get("Gateway") or "Not assigned"),
                dhcp_enabled=dhcp_enabled,
                dns_servers=dns_servers,
            )
        )

    return adapters 