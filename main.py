import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.main_window import WorkTimeTracker

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = WorkTimeTracker()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
