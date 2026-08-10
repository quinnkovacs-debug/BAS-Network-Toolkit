"""Background worker for scanning the selected adapter's subnet."""

import threading

from PySide6.QtCore import QObject, Signal, Slot

from src.models.network_device import NetworkDevice
from src.network.subnet_scanner import scan_subnet


class SubnetScanWorker(QObject):
    """Run a subnet scan without blocking the GUI."""

    host_found = Signal(object)
    progress_changed = Signal(int, int, int)
    completed = Signal(object)
    cancelled = Signal()
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        ipv4_address: str,
        prefix_length: int,
        max_workers: int = 32,
    ) -> None:
        super().__init__()

        self.ipv4_address = ipv4_address
        self.prefix_length = prefix_length
        self.max_workers = max_workers
        self.stop_event = threading.Event()
        self.devices: list[NetworkDevice] = []

    @Slot()
    def run(self) -> None:
        """Run the subnet scan and emit results as they appear."""

        try:
            for host in scan_subnet(
                ipv4_address=self.ipv4_address,
                prefix_length=self.prefix_length,
                stop_event=self.stop_event,
                progress_callback=self.report_progress,
                max_workers=self.max_workers,
            ):
                if self.stop_event.is_set():
                    break

                self.devices.append(host)
                self.host_found.emit(host)

            if self.stop_event.is_set():
                self.cancelled.emit()
            else:
                self.completed.emit(list(self.devices))

        except Exception as error:
            self.failed.emit(str(error))

        finally:
            self.finished.emit()

    def report_progress(
        self,
        scanned: int,
        total: int,
        hosts_found: int,
    ) -> None:
        """Forward scanner progress to the GUI."""

        self.progress_changed.emit(
            scanned,
            total,
            hosts_found,
        )

    def request_stop(self) -> None:
        """Request cancellation of the active scan."""

        self.stop_event.set()