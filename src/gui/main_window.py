"""Main application window for the BAS Network Toolkit."""

from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from src.gui.adapter_panel import AdapterPanel


class MainWindow(QMainWindow):
    """Main BAS Network Toolkit window."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("BAS Network Toolkit")
        self.resize(850, 500)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self) -> None:
        """Create the main-window controls."""

        self.title_label = QLabel("BAS Network Toolkit")
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        self.adapter_panel = AdapterPanel()

    def create_layout(self) -> None:
        """Arrange the main-window controls."""

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.adapter_panel)
        main_layout.addStretch()

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)