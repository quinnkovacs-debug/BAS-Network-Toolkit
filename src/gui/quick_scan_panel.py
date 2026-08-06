"""GUI panel for scanning a local IPv4 subnet."""

from ipaddress import ip_address
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                "IP Address",
                "MAC Address",
                "Ping",
                "HTTP",
                "HTTPS",
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
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

    def create_layout(self) -> None:
        """Arrange the quick-scan controls."""

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_label)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self.title)
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

        row = self.table.rowCount()
        self.table.insertRow(row)

        ip_item = IpAddressItem(host.ip_address)
        mac_item = QTableWidgetItem(
            host.mac_address if host.mac_address else "—"
        )
        ping_item = self.create_status_item(host.ping)
        http_item = self.create_status_item(host.http)
        https_item = self.create_status_item(host.https)    

        self.table.setItem(row, 0, ip_item)
        self.table.setItem(row, 1, mac_item)
        self.table.setItem(row, 2, ping_item)
        self.table.setItem(row, 3, http_item)
        self.table.setItem(row, 4, https_item)


        self.table.setSortingEnabled(sorting_was_enabled)
        

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