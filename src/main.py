"""Application entry point for the BAS Network Toolkit."""

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main() -> int:
    """Start the application and return its exit code."""

    application = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())