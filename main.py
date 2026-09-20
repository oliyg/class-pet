import sys

from PySide6.QtWidgets import QApplication, QLabel


def main() -> int:
    app = QApplication(sys.argv)
    label = QLabel("Hello, PySide6!")
    label.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
