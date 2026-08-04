"""GUI panel for ping and web-interface detection."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.network.target_probe import TargetProbeResult


class TargetPanel(QWidget):
    """Test one IP address for connectivity and web access."""

    scan_requested = Signal(str)
    open_web_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.detected_url: str | None = None

        self.create_widgets()
        self.create_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Create target-panel controls."""

        self.section_title = QLabel("Target Connectivity")
        self.section_title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(
            "Enter controller, switch, or device IP address"
        )

        self.scan_button = QPushButton("Test Target")
        self.open_web_button = QPushButton("Open Web Interface")
        self.open_web_button.setEnabled(False)

        self.status_value = QLabel("Ready")
        self.ping_value = QLabel("—")
        self.http_value = QLabel("—")
        self.https_value = QLabel("—")
        self.web_url_value = QLabel("—")
        self.web_url_value.setTextInteractionFlags(
            self.web_url_value.textInteractionFlags()
        )

    def create_layout(self) -> None:
        """Arrange target-panel controls."""

        target_layout = QHBoxLayout()
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.scan_button)

        details_layout = QFormLayout()
        details_layout.addRow("Status:", self.status_value)
        details_layout.addRow("Ping:", self.ping_value)
        details_layout.addRow("HTTP / TCP 80:", self.http_value)
        details_layout.addRow("HTTPS / TCP 443:", self.https_value)
        details_layout.addRow("Preferred URL:", self.web_url_value)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_web_button)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 15, 0, 0)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.section_title)
        main_layout.addLayout(target_layout)
        main_layout.addLayout(details_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self) -> None:
        """Connect buttons to public signals."""

        self.scan_button.clicked.connect(self.request_scan)
        self.target_input.returnPressed.connect(self.request_scan)
        self.open_web_button.clicked.connect(self.request_open_web)

    def request_scan(self) -> None:
        """Emit a request to scan the entered target."""

        self.scan_requested.emit(self.target_input.text())

    def request_open_web(self) -> None:
        """Emit a request to open the detected web URL."""

        if self.detected_url is not None:
            self.open_web_requested.emit(self.detected_url)

    def set_target(self, target: str) -> None:
        """Set the target address."""

        self.target_input.setText(target)

    def set_scanning(self) -> None:
        """Show that target testing is underway."""

        self.status_value.setText("Testing target...")
        self.scan_button.setEnabled(False)
        self.open_web_button.setEnabled(False)
        self.clear_results()

    def set_error(self, message: str) -> None:
        """Display a target-test error."""

        self.status_value.setText(f"Error: {message}")
        self.scan_button.setEnabled(True)
        self.open_web_button.setEnabled(False)

    def clear_results(self) -> None:
        """Clear previous target results."""

        self.detected_url = None
        self.ping_value.setText("—")
        self.http_value.setText("—")
        self.https_value.setText("—")
        self.web_url_value.setText("—")

    def display_result(self, result: TargetProbeResult) -> None:
        """Display completed connectivity results."""

        self.status_value.setText("Test completed.")
        self.ping_value.setText(
            "Reply received"
            if result.ping_reachable
            else "No reply"
        )
        self.http_value.setText(
            "Available"
            if result.http_available
            else "Not detected"
        )
        self.https_value.setText(
            "Available"
            if result.https_available
            else "Not detected"
        )

        self.detected_url = result.preferred_url

        if self.detected_url is None:
            self.web_url_value.setText(
                "No web port detected"
            )
            self.open_web_button.setEnabled(False)
        else:
            self.web_url_value.setText(self.detected_url)
            self.open_web_button.setEnabled(True)

        self.scan_button.setEnabled(True)