"""Main application window for the BAS Network Toolkit."""

from pathlib import Path
from datetime import datetime
from ipaddress import IPv4Interface
import webbrowser

from PySide6.QtCore import QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.controllers.discovery_worker import DiscoveryWorker
from src.controllers.snmp_correlation_worker import SnmpCorrelationWorker
from src.controllers.subnet_scan_worker import SubnetScanWorker
from src.controllers.target_probe_worker import TargetProbeWorker
from src.gui.adapter_panel import AdapterPanel
from src.gui.discovery_panel import DiscoveryPanel
from src.gui.quick_scan_panel import QuickScanPanel
from src.gui.target_panel import TargetPanel
from src.models.network_device import NetworkDevice
from src.network.discovery_listener import DiscoveryResult
from src.network.target_probe import TargetProbeResult
from src.reports.network_report import build_network_report


class MainWindow(QMainWindow):
    """Main BAS Network Toolkit window."""

    def __init__(self) -> None:
        super().__init__()

        self.discovery_thread: QThread | None = None
        self.discovery_worker: DiscoveryWorker | None = None
        self.last_discovery_result: DiscoveryResult | None = None
        self.target_probe_thread: QThread | None = None
        self.target_probe_worker: TargetProbeWorker | None = None
        self.subnet_scan_thread: QThread | None = None
        self.subnet_scan_worker: SubnetScanWorker | None = None
        self.snmp_correlation_thread: QThread | None = None
        self.snmp_correlation_worker: SnmpCorrelationWorker | None = None

        self.setWindowTitle("BAS Network Toolkit")
        self.resize(1400, 850)

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
        self.target_panel = TargetPanel()
        self.quick_scan_panel = QuickScanPanel()

    def create_layout(self) -> None:
        """Arrange the application into task-specific tabs."""

        # Network Discovery tab
        network_tab = QWidget()
        network_layout = QVBoxLayout()
        network_layout.setContentsMargins(20, 20, 20, 20)
        network_layout.setSpacing(15)

        network_layout.addWidget(self.adapter_panel)
        network_layout.addWidget(self.discovery_panel)
        network_layout.addStretch()

        network_tab.setLayout(network_layout)

        # Quick Scan tab
        quick_scan_tab = QWidget()
        quick_scan_layout = QVBoxLayout()
        quick_scan_layout.setContentsMargins(0, 0, 0, 0)
        quick_scan_layout.setSpacing(0)

        quick_scan_layout.addWidget(self.quick_scan_panel)

        quick_scan_tab.setLayout(quick_scan_layout)

        # Target Tools tab
        target_tools_tab = QWidget()
        target_tools_layout = QVBoxLayout()
        target_tools_layout.setContentsMargins(20, 20, 20, 20)
        target_tools_layout.setSpacing(15)

        target_tools_layout.addWidget(self.target_panel)
        target_tools_layout.addStretch()

        target_tools_tab.setLayout(target_tools_layout)

        # Main tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(network_tab, "Network Discovery")
        self.tabs.addTab(quick_scan_tab, "Quick Scan")
        self.tabs.addTab(target_tools_tab, "Target Tools")

        # Main application layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.tabs)

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

        self.target_panel.scan_requested.connect(
            self.start_target_probe
        )

        self.target_panel.open_web_requested.connect(
            self.open_web_interface
        )

        self.quick_scan_panel.scan_requested.connect(
            self.start_subnet_scan
        )

        self.quick_scan_panel.stop_requested.connect(
            self.stop_subnet_scan
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

        if neighbor.management_address != "Not advertised":
            self.target_panel.set_target(
                neighbor.management_address
            )

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

        if self.subnet_scan_worker is not None:
            self.subnet_scan_worker.request_stop()

        if self.subnet_scan_thread is not None:
            self.subnet_scan_thread.quit()
            if not self.subnet_scan_thread.wait(5000):
                event.ignore()
                QMessageBox.warning(
                    self,
                    "Scan Still Stopping",
                    "The subnet scan is still stopping. Please try closing again.",
                )
                return

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

    def start_target_probe(self, target: str) -> None:
        """Start ping and web-port testing for one target."""

        if self.target_probe_thread is not None:
            self.target_panel.set_error(
                "A target test is already running."
            )
            return

        self.target_panel.set_scanning()

        self.target_probe_thread = QThread()
        self.target_probe_worker = TargetProbeWorker(target)

        self.target_probe_worker.moveToThread(
            self.target_probe_thread
        )

        self.target_probe_thread.started.connect(
            self.target_probe_worker.run
        )

        self.target_probe_worker.completed.connect(
            self.handle_target_probe_result
        )

        self.target_probe_worker.failed.connect(
            self.target_panel.set_error
        )

        self.target_probe_worker.finished.connect(
            self.target_probe_thread.quit
        )

        self.target_probe_worker.finished.connect(
            self.target_probe_worker.deleteLater
        )

        self.target_probe_thread.finished.connect(
            self.target_probe_thread.deleteLater
        )

        self.target_probe_thread.finished.connect(
            self.clear_target_probe_thread
        )

        self.target_probe_thread.start()

    


    def handle_target_probe_result(
        self,
        result: TargetProbeResult,
    ) -> None:
        """Display one target-probe result."""

        self.target_panel.display_result(result)


    def clear_target_probe_thread(self) -> None:
        """Clear completed target-worker references."""

        self.target_probe_thread = None
        self.target_probe_worker = None


    def open_web_interface(self, url: str) -> None:
        """Open a detected web interface in the default browser."""

        webbrowser.open(url)

    def start_subnet_scan(self) -> None:
        """Start scanning the selected adapter's local subnet."""

        if self.subnet_scan_thread is not None:
            self.quick_scan_panel.set_error(
                "A subnet scan is already running."
            )
            return

        adapter = self.adapter_panel.selected_adapter()

        if adapter is None:
            self.quick_scan_panel.set_error(
                "No network adapter is selected."
            )
            return

        if adapter.status.lower() != "up":
            self.quick_scan_panel.set_error(
                "The selected adapter is not connected."
            )
            return

        if adapter.prefix_length is None:
            self.quick_scan_panel.set_error(
                "The selected adapter has no IPv4 prefix length."
            )
            return

        if adapter.ipv4_address == "Not assigned":
            self.quick_scan_panel.set_error(
                "The selected adapter has no IPv4 address."
            )
            return

        interface = IPv4Interface(
            f"{adapter.ipv4_address}/{adapter.prefix_length}"
        )

        prefix_length = interface.network.prefixlen

        if prefix_length < 23:
            self.quick_scan_panel.set_error(
                "Networks larger than /23 are not supported."
            )
            return

        if prefix_length == 23:
            answer = QMessageBox.question(
                self,
                "Confirm /23 Scan",
                (
                    f"{interface.network} contains "
                    f"{interface.network.num_addresses - 2} usable addresses.\n\n"
                    "Continue with the subnet scan?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        total_hosts = interface.network.num_addresses - 2

        self.quick_scan_panel.begin_scan(
            network_description=str(interface.network),
            total_hosts=total_hosts,
        )

        self.subnet_scan_thread = QThread()

        self.subnet_scan_worker = SubnetScanWorker(
            ipv4_address=adapter.ipv4_address,
            prefix_length=adapter.prefix_length,
            max_workers=32,
        )

        self.subnet_scan_worker.moveToThread(
            self.subnet_scan_thread
        )

        self.subnet_scan_thread.started.connect(
            self.subnet_scan_worker.run
        )

        self.subnet_scan_worker.host_found.connect(
            self.quick_scan_panel.add_host
        )

        self.subnet_scan_worker.progress_changed.connect(
            self.quick_scan_panel.update_progress
        )

        self.subnet_scan_worker.completed.connect(
            self.handle_subnet_scan_completed
        )

        self.subnet_scan_worker.cancelled.connect(
            self.quick_scan_panel.set_cancelled
        )

        self.subnet_scan_worker.failed.connect(
            self.quick_scan_panel.set_error
        )

        self.subnet_scan_worker.finished.connect(
            self.subnet_scan_thread.quit
        )

        self.subnet_scan_worker.finished.connect(
            self.subnet_scan_worker.deleteLater
        )

        self.subnet_scan_thread.finished.connect(
            self.subnet_scan_thread.deleteLater
        )

        self.subnet_scan_thread.finished.connect(
            self.clear_subnet_scan_thread
        )

        self.subnet_scan_thread.start()


    def stop_subnet_scan(self) -> None:
        """Request cancellation of the active subnet scan."""

        if self.subnet_scan_worker is None:
            return

        self.quick_scan_panel.set_stopping()
        self.subnet_scan_worker.request_stop()


    def clear_subnet_scan_thread(self) -> None:
        """Clear completed subnet-scan worker references."""

        self.subnet_scan_thread = None
        self.subnet_scan_worker = None

    def handle_subnet_scan_completed(
        self,
        devices: list[NetworkDevice],
    ) -> None:
        """Finish Quick Scan or begin optional SNMP correlation."""

        if not self.quick_scan_panel.snmp_enabled.isChecked():
            self.quick_scan_panel.set_completed()
            return

        switch_ip = self.quick_scan_panel.switch_ip_input.text().strip()
        community = self.quick_scan_panel.community_input.text().strip()
        vlan_id = self.quick_scan_panel.vlan_input.value()

        if not switch_ip:
            self.quick_scan_panel.snmp_status_label.setText(
                "SNMP skipped: Switch IP is required."
            )
            self.quick_scan_panel.set_completed()
            return

        if not community:
            self.quick_scan_panel.snmp_status_label.setText(
                "SNMP skipped: Community string is required."
            )
            self.quick_scan_panel.set_completed()
            return

        try:
            community.encode("latin-1")
        except UnicodeEncodeError:
            self.quick_scan_panel.snmp_status_label.setText(
                "SNMP skipped: Community contains unsupported characters."
            )
            self.quick_scan_panel.set_completed()
            return

        self.start_snmp_correlation(
            devices=devices,
            switch_ip=switch_ip,
            community=community,
            vlan_id=vlan_id,
        )

    def start_snmp_correlation(
        self,
        devices: list[NetworkDevice],
        switch_ip: str,
        community: str,
        vlan_id: int,
    ) -> None:
        """Start SNMP MAC-to-switch-port correlation."""

        if self.snmp_correlation_thread is not None:
            self.quick_scan_panel.snmp_status_label.setText(
                "SNMP correlation is already running."
            )
            return

        self.quick_scan_panel.snmp_status_label.setText(
            "Querying switch MAC table..."
        )

        self.snmp_correlation_thread = QThread()

        self.snmp_correlation_worker = SnmpCorrelationWorker(
            devices=devices,
            switch_ip=switch_ip,
            community=community,
            vlan_id=vlan_id,
        )

        self.snmp_correlation_worker.moveToThread(
            self.snmp_correlation_thread
        )

        self.snmp_correlation_thread.started.connect(
            self.snmp_correlation_worker.run
        )

        self.snmp_correlation_worker.device_enriched.connect(
            self.handle_snmp_device_enriched
        )

        self.snmp_correlation_worker.completed.connect(
            self.handle_snmp_correlation_completed
        )

        self.snmp_correlation_worker.failed.connect(
            self.handle_snmp_correlation_failed
        )

        self.snmp_correlation_worker.finished.connect(
            self.snmp_correlation_thread.quit
        )

        self.snmp_correlation_worker.finished.connect(
            self.snmp_correlation_worker.deleteLater
        )

        self.snmp_correlation_thread.finished.connect(
            self.snmp_correlation_thread.deleteLater
        )

        self.snmp_correlation_thread.finished.connect(
            self.clear_snmp_correlation_thread
        )

        self.snmp_correlation_thread.start()

    def handle_snmp_device_enriched(
        self,
        device: NetworkDevice,
    ) -> None:
        """Update Quick Scan with one correlated device."""

        self.quick_scan_panel.update_device(device)

    def handle_snmp_correlation_completed(
        self,
        matched: int,
        total: int,
    ) -> None:
        """Handle successful SNMP correlation completion."""

        self.quick_scan_panel.snmp_status_label.setText(
            f"Correlation complete: {matched} of {total} devices matched."
        )

        self.quick_scan_panel.set_completed()

    def handle_snmp_correlation_failed(
        self,
        message: str,
    ) -> None:
        """Handle an SNMP correlation failure."""

        self.quick_scan_panel.snmp_status_label.setText(
            f"SNMP correlation failed: {message}"
        )

        # The subnet scan itself was still successful.
        self.quick_scan_panel.set_completed()

    def clear_snmp_correlation_thread(self) -> None:
        """Clear completed SNMP worker references."""

        self.snmp_correlation_thread = None
        self.snmp_correlation_worker = None