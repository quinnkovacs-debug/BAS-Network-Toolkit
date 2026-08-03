"""Background worker for LLDP/CDP discovery."""

from PySide6.QtCore import QObject, Signal, Slot

from src.network.capture_interface import find_capture_interface
from src.network.discovery_listener import (
    DiscoveryResult,
    listen_for_discovery,
)
from src.network.adapter_manager import NetworkAdapter
import threading


class DiscoveryWorker(QObject):
    """Run switch discovery without blocking the GUI."""

    completed = Signal(object)
    timed_out = Signal()
    cancelled = Signal()
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        adapter: NetworkAdapter,
        timeout_seconds: int = 60,
    ) -> None:
        super().__init__()

        self.adapter = adapter
        self.timeout_seconds = timeout_seconds
        self.stop_event = threading.Event()

    @Slot()
    def run(self) -> None:
        """Run one LLDP/CDP discovery attempt."""

        try:
            capture_interface = find_capture_interface(
                adapter_name=self.adapter.name,
                mac_address=self.adapter.mac_address,
            )

            result: DiscoveryResult | None = listen_for_discovery(
                capture_interface=capture_interface,
                timeout_seconds=self.timeout_seconds,
                stop_event=self.stop_event,
            )

            if self.stop_event.is_set():
                self.cancelled.emit()
            elif result is None:
                self.timed_out.emit()
            else:
                self.completed.emit(result)

        except Exception as error:
            self.failed.emit(str(error))

        finally:
            self.finished.emit()

    def request_stop(self) -> None:
        """Request cancellation of the active capture."""

        self.stop_event.set()