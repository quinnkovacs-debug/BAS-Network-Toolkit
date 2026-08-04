"""Background worker for testing one network target."""

from PySide6.QtCore import QObject, Signal, Slot

from src.network.target_probe import (
    TargetProbeResult,
    probe_target,
)


class TargetProbeWorker(QObject):
    """Run target connectivity tests outside the GUI thread."""

    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, target: str) -> None:
        super().__init__()
        self.target = target

    @Slot()
    def run(self) -> None:
        """Run the target probe."""

        try:
            result: TargetProbeResult = probe_target(self.target)
            self.completed.emit(result)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()