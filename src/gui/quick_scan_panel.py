"""GUI panel for scanning a local IPv4 subnet."""

from ipaddress import ip_address
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.network.subnet_scanner import NetworkDevice


class IpAddressItem(QTableWidgetItem):
    """Table item that sorts IPv4 addresses numerically."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return ip_address(self.text()) < ip_address(other.text())
        except ValueError:
            return self.text() < other.text()


class QuickScanPanel(QWidget):
    """Display subnet-scan controls, progress, and results."""

    scan_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.create_widgets()
        self.devices_by_ip: dict[str, NetworkDevice] = {}
        self.create_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Create the quick-scan controls."""

        self.title = QLabel("Quick Scan")
        self.title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        self.scan_button = QPushButton("Scan Subnet")

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

        self.status_label = QLabel("Ready")

        self.progress_label = QLabel("0 / 0 — 0 devices found")

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels(
            [
                "IP Address",
                "MAC Address",
                "Manufacturer",
                "Switch",
                "Port",
                "Vlan",
                "Ping",
                "HTTP",
                "HTTPS",
                "FOX",
                "FOXS",
                "Modbus",
                "Bacnet",   
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            9,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            10,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            11,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            12,
            QHeaderView.ResizeMode.ResizeToContents,
        ) 

        self.snmp_enabled = QCheckBox("Enable SNMP switch correlation")

        self.switch_ip_input = QLineEdit()
        self.switch_ip_input.setPlaceholderText("Switch management IP")

        self.community_input = QLineEdit()
        self.community_input.setPlaceholderText("SNMPv2c community")
        self.community_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.vlan_input = QSpinBox()
        self.vlan_input.setRange(1, 4094)
        self.vlan_input.setValue(1)

        self.snmp_status_label = QLabel("SNMP correlation disabled")
        self.set_snmp_controls_enabled(False)
        self.bas_only_checkbox = QCheckBox(
            "Show BAS devices only"
        )

    def create_layout(self) -> None:
        """Arrange the quick-scan controls."""

        snmp_layout = QFormLayout()

        snmp_layout.addRow(
            self.snmp_enabled
        )

        snmp_layout.addRow(
            "Switch IP:",
            self.switch_ip_input,
        )

        snmp_layout.addRow(
            "Community:",
            self.community_input,
        )

        snmp_layout.addRow(
            "VLAN:",
            self.vlan_input,
        )

        snmp_layout.addRow(
            "SNMP Status:",
            self.snmp_status_label,
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.bas_only_checkbox)
        button_layout.addStretch()

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_label)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self.title)
        layout.addLayout(snmp_layout)
        layout.addLayout(button_layout)
        layout.addLayout(status_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.table, 1)

        self.setLayout(layout)

    def connect_signals(self) -> None:
        """Connect controls to the panel's public signals."""

        self.scan_button.clicked.connect(
            self.scan_requested.emit
        )
        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

        self.snmp_enabled.toggled.connect(
            self.set_snmp_controls_enabled
        )

        self.bas_only_checkbox.toggled.connect(
            self.apply_bas_filter
        )

    def set_snmp_controls_enabled(
        self,
        enabled: bool,
    ) -> None:
        """Enable or disable SNMP configuration controls."""

        self.switch_ip_input.setEnabled(enabled)
        self.community_input.setEnabled(enabled)
        self.vlan_input.setEnabled(enabled)

        if enabled:
            self.snmp_status_label.setText(
                "SNMP correlation enabled"
            )
        else:
            self.snmp_status_label.setText(
                "SNMP correlation disabled"
            )

    def begin_scan(
        self,
        network_description: str,
        total_hosts: int,
    ) -> None:
        """Prepare the panel for a new scan."""

        self.clear_results()

        self.status_label.setText(
            f"Scanning {network_description}..."
        )
        self.progress_label.setText(
            f"0 / {total_hosts} — 0 devices found"
        )

        self.progress.setMinimum(0)
        self.progress.setMaximum(total_hosts)
        self.progress.setValue(0)

        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def update_progress(
        self,
        scanned: int,
        total: int,
        hosts_found: int,
    ) -> None:
        """Update scan progress."""

        self.progress.setMaximum(total)
        self.progress.setValue(scanned)

        self.progress_label.setText(
            f"{scanned} / {total} — "
            f"{hosts_found} devices found"
        )

    def add_host(self, host: NetworkDevice) -> None:
        """Add one responsive host to the results table."""

        sorting_was_enabled = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.devices_by_ip[host.ip_address] = host

        row = self.table.rowCount()
        self.table.insertRow(row)

        ip_item = IpAddressItem(host.ip_address)

        mac_item = QTableWidgetItem(
            host.mac_address if host.mac_address else "—"
        )

        vendor_item = QTableWidgetItem(
            host.vendor if host.vendor else "—"
        )

        switch_item = QTableWidgetItem(
            host.switch_name if host.switch_name else "—"
        )

        port_item = QTableWidgetItem(
            host.switch_port if host.switch_port else "—"
        )

        vlan_item = QTableWidgetItem(
            host.vlan_id if host.vlan_id else "—"
        )

        ping_item = self.create_status_item(host.ping)
        http_item = self.create_status_item(host.http)
        https_item = self.create_status_item(host.https)
        fox_item = self.create_status_item(
            1911 in host.tcp_ports
        )

        foxs_item = self.create_status_item(
            4911 in host.tcp_ports
        )

        modbus_item = self.create_status_item(
            502 in host.tcp_ports
        )

        bacnet_ports = sorted(
            int(service.split(":", 1)[1])
            for service in host.udp_services
            if service.startswith("BACnet:")
        )

        bacnet_item = QTableWidgetItem(
            ", ".join(str(port) for port in bacnet_ports)
            if bacnet_ports
            else "—"
        )

        self.table.setItem(row, 0, ip_item)
        self.table.setItem(row, 1, mac_item)
        self.table.setItem(row, 2, vendor_item)
        self.table.setItem(row, 3, switch_item)
        self.table.setItem(row, 4, port_item)
        self.table.setItem(row, 5, vlan_item)
        self.table.setItem(row, 6, ping_item)
        self.table.setItem(row, 7, http_item)
        self.table.setItem(row, 8, https_item)
        self.table.setItem(row, 9, fox_item)
        self.table.setItem(row, 10, foxs_item)
        self.table.setItem(row, 11, modbus_item)
        self.table.setItem(row, 12, bacnet_item)
        self.table.setSortingEnabled(sorting_was_enabled)

        self.apply_bas_filter()

    @staticmethod
    def create_status_item(available: bool) -> QTableWidgetItem:
        """Create a centered availability indicator."""

        item = QTableWidgetItem("✓" if available else "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        return item

    def set_completed(self) -> None:
        """Show that the scan completed."""

        self.table.sortItems(
            0,
            Qt.SortOrder.AscendingOrder,
        )

        self.status_label.setText("Scan completed.")
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def set_stopping(self) -> None:
        """Show that cancellation was requested."""

        self.status_label.setText("Stopping scan...")
        self.stop_button.setEnabled(False)

    def set_cancelled(self) -> None:
        """Show that the scan was cancelled."""

        self.status_label.setText("Scan stopped.")
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def set_error(self, message: str) -> None:
        """Display a scan error."""

        self.status_label.setText(f"Error: {message}")
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def clear_results(self) -> None:
        """Remove all previous scan results."""

        self.table.setRowCount(0)
        self.progress.setValue(0)
        self.devices_by_ip.clear()

    def update_device(
        self,
        device: NetworkDevice,
    ) -> None:
        """Update an existing Quick Scan row with enriched device data."""

        self.devices_by_ip[device.ip_address] = device
        sorting_was_enabled = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)

        try:
            for row in range(self.table.rowCount()):
                ip_item = self.table.item(row, 0)

                if ip_item is None:
                    continue

                if ip_item.text() != device.ip_address:
                    continue

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        device.mac_address
                        if device.mac_address
                        else "—"
                    ),
                )

                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        device.switch_name
                        if device.switch_name
                        else "—"
                    ),
                )

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        device.switch_port
                        if device.switch_port
                        else "—"
                    ),
                )

                self.table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        device.vlan_id
                        if device.vlan_id
                        else "—"
                    ),
                )

                bacnet_ports = sorted(
                    int(service.split(":", 1)[1])
                    for service in device.udp_services
                    if service.startswith("BACnet:")
                )

                self.table.setItem(
                    row,
                    12,
                    QTableWidgetItem(
                        ", ".join(str(port) for port in bacnet_ports)
                        if bacnet_ports
                        else "—"
                    ),
                )

                break

        finally:
            self.table.setSortingEnabled(sorting_was_enabled)

        self.apply_bas_filter()

    def apply_bas_filter(self) -> None:
        """Show all devices or only devices classified as BAS."""

        bas_only = self.bas_only_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            ip_item = self.table.item(row, 0)

            if ip_item is None:
                continue

            device = self.devices_by_ip.get(
                ip_item.text()
            )

            if device is None:
                self.table.setRowHidden(
                    row,
                    bas_only,
                )
                continue

            hide_row = (
                bas_only
                and not device.is_bas_device
            )

            self.table.setRowHidden(
                row,
                hide_row,
            )