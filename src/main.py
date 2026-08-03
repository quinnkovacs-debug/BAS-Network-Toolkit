"""Main application window for BAS Network Toolkit."""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from network.adapter_manager import NetworkAdapter, get_network_adapters


class MainWindow(QMainWindow):
    """Main BAS Network Toolkit window."""

    def __init__(self) -> None:
        super().__init__()

        self.adapters: list[NetworkAdapter] = []

        self.setWindowTitle("BAS Network Toolkit")
        self.resize(850, 500)

        self.create_widgets()
        self.create_layout()
        self.connect_signals()

        self.refresh_adapters()

    def create_widgets(self) -> None:
        """Create the controls displayed in the window."""

        self.title_label = QLabel("BAS Network Toolkit")
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        self.description_label = QLabel(
            "Select the network adapter connected to the customer network."
        )

        self.adapter_selector = QComboBox()
        self.adapter_selector.setMinimumWidth(500)

        self.refresh_button = QPushButton("Refresh Adapters")

        self.status_value = QLabel("—")
        self.speed_value = QLabel("—")
        self.mac_value = QLabel("—")
        self.index_value = QLabel("—")

    def create_layout(self) -> None:
        """Arrange the controls in the window."""

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(self.adapter_selector)
        selector_layout.addWidget(self.refresh_button)

        details_layout = QFormLayout()
        details_layout.addRow("Link status:", self.status_value)
        details_layout.addRow("Link speed:", self.speed_value)
        details_layout.addRow("MAC address:", self.mac_value)
        details_layout.addRow("Interface index:", self.index_value)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.description_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(selector_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(details_layout)
        main_layout.addStretch()

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    def connect_signals(self) -> None:
        """Connect user actions to application functions."""

        self.refresh_button.clicked.connect(self.refresh_adapters)
        self.adapter_selector.currentIndexChanged.connect(
            self.update_adapter_details
        )

    def refresh_adapters(self) -> None:
        """Reload the network-adapter list from Windows."""

        self.adapter_selector.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.adapter_selector.clear()
        self.adapters.clear()

        try:
            self.adapters = get_network_adapters()
        except (RuntimeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Adapter Discovery Error",
                str(error),
            )
            self.clear_adapter_details()
            return
        finally:
            self.refresh_button.setEnabled(True)

        for adapter in self.adapters:
            self.adapter_selector.addItem(adapter.display_name)

        if self.adapters:
            self.adapter_selector.setEnabled(True)

            preferred_index = self.find_preferred_adapter()
            self.adapter_selector.setCurrentIndex(preferred_index)
            self.update_adapter_details(preferred_index)
        else:
            self.adapter_selector.addItem("No network adapters found")
            self.clear_adapter_details()

    def find_preferred_adapter(self) -> int:
        """Prefer a connected Ethernet adapter when possible."""

        for index, adapter in enumerate(self.adapters):
            adapter_text = (
                f"{adapter.name} {adapter.description}"
            ).lower()

            is_connected = adapter.status.lower() == "up"
            appears_wired = (
                "ethernet" in adapter_text
                or "gbe" in adapter_text
                or "gigabit" in adapter_text
            )

            if is_connected and appears_wired:
                return index

        for index, adapter in enumerate(self.adapters):
            if adapter.status.lower() == "up":
                return index

        return 0

    def update_adapter_details(self, index: int) -> None:
        """Display information for the selected adapter."""

        if index < 0 or index >= len(self.adapters):
            self.clear_adapter_details()
            return

        adapter = self.adapters[index]

        self.status_value.setText(adapter.status)
        self.speed_value.setText(adapter.link_speed)
        self.mac_value.setText(adapter.mac_address)
        self.index_value.setText(str(adapter.interface_index))

    def clear_adapter_details(self) -> None:
        """Clear the adapter-information fields."""

        self.status_value.setText("—")
        self.speed_value.setText("—")
        self.mac_value.setText("—")
        self.index_value.setText("—")


def main() -> int:
    """Start the application."""

    application = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())