"""Background worker for BACnet/IP subnet discovery."""

from PySide6.QtCore import QObject, Signal, Slot

from src.models.network_device import NetworkDevice
from src.network.bacnet_probe import discover_bacnet_subnet


class BacnetDiscoveryWorker(QObject):
    """Discover BACnet/IP devices across the selected subnet."""

    device_enriched = Signal(object)

    completed = Signal(int, int)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        devices: list[NetworkDevice],
        local_interface_ip: str,
        broadcast_ip: str,
    ) -> None:
        super().__init__()

        self.devices = list(devices)
        self.local_interface_ip = local_interface_ip
        self.broadcast_ip = broadcast_ip

    @Slot()
    def run(self) -> None:
        """Run BACnet discovery without blocking the GUI."""

        try:
            discovered = discover_bacnet_subnet(
                local_interface_ip=self.local_interface_ip,
                broadcast_ip=self.broadcast_ip,
            )

            matched = 0

            devices_by_ip = {
                device.ip_address: device
                for device in self.devices
            }

            for ip_address, ports in discovered.items():
                device = devices_by_ip.get(ip_address)

                if device is None:
                    continue

                for port in sorted(ports):
                    device.udp_services.add(
                        f"BACnet:{port}"
                    )

                matched += 1
                self.device_enriched.emit(device)

            self.completed.emit(
                matched,
                len(self.devices),
            )

        except Exception as error:
            message = str(error) or repr(error)

            self.failed.emit(
                f"{type(error).__name__}: {message}"
            )

        finally:
            self.finished.emit()