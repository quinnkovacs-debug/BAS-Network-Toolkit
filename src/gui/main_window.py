"""Main application window for the BAS Network Toolkit."""

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from src.gui.adapter_panel import AdapterPanel
from src.gui.discovery_panel import DiscoveryPanel
from PySide6.QtCore import QThread

from src.controllers.discovery_worker import DiscoveryWorker
from src.network.discovery_listener import DiscoveryResult
from PySide6.QtGui import QCloseEvent
from src.reports.network_report import build_network_report
from datetime import datetime


class MainWindow(QMainWindow):
    """Main BAS Network Toolkit window."""

    def __init__(self) -> None:
        super().__init__()

        self.discovery_thread: QThread | None = None
        self.discovery_worker: DiscoveryWorker | None = None
        self.last_discovery_result: DiscoveryResult | None = None

        self.setWindowTitle("BAS Network Toolkit")
        self.resize(850, 500)

        self.create_widgets()
        self.create_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Create the main-window controls."""

        self.title_label = QLabel("BAS Network Toolkit")
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        self.adapter_panel = AdapterPanel()
        self.discovery_panel = DiscoveryPanel()

    def create_layout(self) -> None:
        """Arrange the main-window controls."""

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.adapter_panel)
        main_layout.addWidget(self.discovery_panel)
        main_layout.addStretch()

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def connect_signals(self) -> None:
        """Connect GUI signals to main-window handlers."""

        self.discovery_panel.discover_requested.connect(
            self.start_discovery
        )

        self.discovery_panel.stop_requested.connect(
            self.stop_discovery
        )

        self.discovery_panel.copy_requested.connect(
            self.copy_results
        )

        self.discovery_panel.save_requested.connect(
            self.save_report
        )


    def start_discovery(self) -> None:
        """Start LLDP/CDP discovery for the selected adapter."""

        adapter = self.adapter_panel.selected_adapter()

        if adapter is None:
            self.discovery_panel.set_error(
                "No network adapter is selected."
            )
            return

        if adapter.status.lower() != "up":
            self.discovery_panel.set_error(
                "The selected adapter is not connected."
            )
            return
        self.last_discovery_result = None
        self.discovery_panel.clear_results()
        self.discovery_panel.set_listening(adapter.name)

        self.discovery_thread = QThread()
        self.discovery_worker = DiscoveryWorker(
            adapter=adapter,
            timeout_seconds=60,
        )

        self.discovery_worker.moveToThread(
            self.discovery_thread
        )

        self.discovery_thread.started.connect(
            self.discovery_worker.run
        )

        self.discovery_worker.completed.connect(
            self.handle_discovery_result
        )

        self.discovery_worker.timed_out.connect(
            self.discovery_panel.set_timeout
        )

        self.discovery_worker.failed.connect(
            self.discovery_panel.set_error
        )

        self.discovery_worker.finished.connect(
            self.discovery_thread.quit
        )

        self.discovery_worker.finished.connect(
            self.discovery_worker.deleteLater
        )

        self.discovery_thread.finished.connect(
            self.discovery_thread.deleteLater
        )

        self.discovery_thread.finished.connect(
            self.clear_discovery_thread
        )

        self.discovery_worker.cancelled.connect(
            self.discovery_panel.set_cancelled
        )

        self.discovery_thread.start()


    def handle_discovery_result(
        self,
        result: DiscoveryResult,
    ) -> None:
        """Display one discovery result."""

        if result.lldp_neighbor is None:
            self.discovery_panel.set_error(
                f"{result.protocol} was detected, but parsing is not implemented."
            )
            return

        neighbor = result.lldp_neighbor

        self.last_discovery_result = result

        self.discovery_panel.display_lldp_result(
            protocol=result.protocol,
            switch_name=neighbor.system_name,
            switch_port=neighbor.port_id,
            port_description=neighbor.port_description,
            management_ip=neighbor.management_address,
            vlan_id=neighbor.vlan_id,
            source_mac=neighbor.source_mac,
            system_description=neighbor.system_description,
        )


    def stop_discovery(self) -> None:
        """Request cancellation of the current discovery operation."""

        if self.discovery_worker is None:
            return

        self.discovery_panel.set_stopping()
        self.discovery_worker.request_stop()


    def clear_discovery_thread(self) -> None:
        """Clear references after the worker thread exits."""

        self.discovery_thread = None
        self.discovery_worker = None

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop active discovery cleanly before closing."""

        if self.discovery_worker is None or self.discovery_thread is None:
            event.accept()
            return

        self.discovery_panel.set_stopping()
        self.discovery_worker.request_stop()

        if self.discovery_thread.wait(3000):
            event.accept()
        else:
            event.ignore()
            self.discovery_panel.set_error(
                "Discovery did not stop within 3 seconds."
            )

    def create_current_report(self) -> str | None:
        """Build a report from the selected adapter and latest result."""

        adapter = self.adapter_panel.selected_adapter()

        if adapter is None:
            self.discovery_panel.set_error(
                "No network adapter is selected."
            )
            return None

        if self.last_discovery_result is None:
            self.discovery_panel.set_error(
                "No discovery result is available."
            )
            return None

        return build_network_report(
            adapter=adapter,
            discovery_result=self.last_discovery_result,
        )


    def copy_results(self) -> None:
        """Copy the current network report to the clipboard."""

        report = self.create_current_report()

        if report is None:
            return

        QApplication.clipboard().setText(report)

        self.discovery_panel.status_value.setText(
            "Results copied to clipboard."
        )


    def save_report(self) -> None:
        """Save the current network report as a text file."""

        report = self.create_current_report()

        if report is None:
            return

        adapter = self.adapter_panel.selected_adapter()

        adapter_name = "network"

        if adapter is not None:
            adapter_name = (
                adapter.name
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
            )

        default_filename = (
            f"BAS_Network_Report_"
            f"{adapter_name}_"
            f"{datetime.now():%Y%m%d_%H%M%S}.txt"
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Network Report",
            default_filename,
            "Text Files (*.txt);;All Files (*.*)",
        )

        if not filename:
            return

        try:
            Path(filename).write_text(
                report,
                encoding="utf-8",
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Save Report Error",
                str(error),
            )
            return

        self.discovery_panel.status_value.setText(
            f"Report saved to {filename}"
        )