"""GUI panel for displaying switch discovery results."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiscoveryPanel(QWidget):
    """Display LLDP/CDP discovery controls and results."""

    discover_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.create_widgets()
        self.create_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Create the discovery-panel controls."""

        self.section_title = QLabel("Switch Discovery")
        self.section_title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        self.status_value = QLabel("Ready")

        self.switch_name_value = QLabel("—")
        self.switch_port_value = QLabel("—")
        self.port_description_value = QLabel("—")
        self.management_ip_value = QLabel("—")
        self.vlan_value = QLabel("—")
        self.protocol_value = QLabel("—")
        self.source_mac_value = QLabel("—")
        self.system_description_value = QLabel("—")
        self.system_description_value.setWordWrap(True)

        self.discover_button = QPushButton("Discover")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

    def create_layout(self) -> None:
        """Arrange the discovery-panel controls."""

        details_layout = QFormLayout()
        details_layout.addRow("Status:", self.status_value)
        details_layout.addRow("Switch Name:", self.switch_name_value)
        details_layout.addRow("Switch Port:", self.switch_port_value)
        details_layout.addRow(
            "Port Description:",
            self.port_description_value,
        )
        details_layout.addRow(
            "Management IP:",
            self.management_ip_value,
        )
        details_layout.addRow("Native VLAN:", self.vlan_value)
        details_layout.addRow("Protocol:", self.protocol_value)
        details_layout.addRow("Source MAC:", self.source_mac_value)
        details_layout.addRow(
            "System Description:",
            self.system_description_value,
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.discover_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 15, 0, 0)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.section_title)
        main_layout.addLayout(details_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self) -> None:
        """Connect buttons to public panel signals."""

        self.discover_button.clicked.connect(
            self.discover_requested.emit
        )
        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

    def set_listening(self, adapter_name: str) -> None:
        """Show that packet discovery is in progress."""

        self.status_value.setText(
            f"Listening on {adapter_name} for LLDP/CDP..."
        )
        self.discover_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def set_ready(self) -> None:
        """Return the panel to its idle state."""

        self.status_value.setText("Ready")
        self.discover_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def set_error(self, message: str) -> None:
        """Display a discovery error."""

        self.status_value.setText(f"Error: {message}")
        self.discover_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def set_timeout(self) -> None:
        """Display a discovery timeout."""

        self.status_value.setText(
            "No LLDP or CDP packet received before timeout."
        )
        self.discover_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def clear_results(self) -> None:
        """Clear all displayed switch information."""

        self.switch_name_value.setText("—")
        self.switch_port_value.setText("—")
        self.port_description_value.setText("—")
        self.management_ip_value.setText("—")
        self.vlan_value.setText("—")
        self.protocol_value.setText("—")
        self.source_mac_value.setText("—")
        self.system_description_value.setText("—")

    def display_lldp_result(
        self,
        protocol: str,
        switch_name: str,
        switch_port: str,
        port_description: str,
        management_ip: str,
        vlan_id: str,
        source_mac: str,
        system_description: str,
    ) -> None:
        """Display one parsed LLDP result."""

        self.status_value.setText("Discovery completed.")
        self.protocol_value.setText(protocol)
        self.switch_name_value.setText(switch_name)
        self.switch_port_value.setText(switch_port)
        self.port_description_value.setText(port_description)
        self.management_ip_value.setText(management_ip)
        self.vlan_value.setText(vlan_id)
        self.source_mac_value.setText(source_mac)
        self.system_description_value.setText(system_description)

        self.discover_button.setEnabled(True)
        self.stop_button.setEnabled(False)