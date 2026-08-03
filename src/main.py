import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BAS Field Toolkit")
        self.resize(900, 600)

        title = QLabel("BAS Field Toolkit")
        title.setStyleSheet("font-size:24px; font-weight:bold;")

        description = QLabel(
            "Welcome! This application will help discover network information."
        )

        discover_button = QPushButton("Discover")
        discover_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(discover_button)
        layout.addStretch()

        central = QWidget()
        central.setLayout(layout)

        self.setCentralWidget(central)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()