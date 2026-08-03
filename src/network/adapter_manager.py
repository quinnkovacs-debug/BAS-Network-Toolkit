"""Windows network-adapter discovery functions."""

import json
import subprocess
from dataclasses import dataclass


@dataclass
class NetworkAdapter:
    """Information about one Windows network adapter."""

    name: str
    description: str
    interface_index: int
    status: str
    link_speed: str
    mac_address: str

    @property
    def display_name(self) -> str:
        """Return the text displayed in the adapter selector."""

        return f"{self.name} — {self.description}"


def get_network_adapters() -> list[NetworkAdapter]:
    """Return the network adapters reported by Windows."""

    powershell_command = """
        Get-NetAdapter |
        Sort-Object Name |
        Select-Object Name,
                      InterfaceDescription,
                      ifIndex,
                      Status,
                      LinkSpeed,
                      MacAddress |
        ConvertTo-Json -Depth 3
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

    raw_adapters = json.loads(output)

    # ConvertTo-Json returns a dictionary when Windows finds only one adapter
    # and a list when it finds multiple adapters.
    if isinstance(raw_adapters, dict):
        raw_adapters = [raw_adapters]

    adapters: list[NetworkAdapter] = []

    for raw_adapter in raw_adapters:
        adapters.append(
            NetworkAdapter(
                name=str(raw_adapter.get("Name") or "Unknown"),
                description=str(
                    raw_adapter.get("InterfaceDescription") or "Unknown adapter"
                ),
                interface_index=int(raw_adapter.get("ifIndex") or 0),
                status=str(raw_adapter.get("Status") or "Unknown"),
                link_speed=str(raw_adapter.get("LinkSpeed") or "Unknown"),
                mac_address=str(raw_adapter.get("MacAddress") or "Not available"),
            )
        )

    return adapters