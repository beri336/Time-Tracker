from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton, QLabel

from .config import Config as _conf


class ButtonStyle:
    @staticmethod
    def action_button_style(button: QPushButton):
        button.setMinimumHeight(45)
        button.setFont(QFont(_conf.font, 11))
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #1f2937;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover  { background-color: #e5e7eb; border-color: #d1d5db; }
            QPushButton:pressed { background-color: #2563eb; color: white; }
            QPushButton:disabled { background-color: #f9fafb; color: #9ca3af; }
        """)

    @staticmethod
    def layout_button_style(button: QPushButton):
        button.setMinimumHeight(45)
        button.setFont(QFont(_conf.font, 11))
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover   { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
            QPushButton:disabled { background-color: #9ca3af; }
        """)

class ModernButton(QPushButton):
    def __init__(self, text: str, primary: bool = False):
        super().__init__(text)
        self.setMinimumHeight(45)
        self.setFont(QFont(_conf.font, 11))
        self.setCursor(Qt.PointingHandCursor)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb; color: white;
                    border: none; border-radius: 8px;
                    padding: 10px 20px; font-weight: 600;
                }
                QPushButton:hover   { background-color: #1d4ed8; }
                QPushButton:pressed { background-color: #1e40af; }
                QPushButton:disabled { background-color: #9ca3af; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6; color: #1f2937;
                    border: 1px solid #e5e7eb; border-radius: 8px;
                    padding: 10px 20px; font-weight: 500;
                }
                QPushButton:hover   { background-color: #e5e7eb; border-color: #d1d5db; }
                QPushButton:pressed { background-color: #d1d5db; }
                QPushButton:disabled { background-color: #f9fafb; color: #9ca3af; }
            """)

def main_window_style() -> str:
    return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #f5f7fa, stop:1 #e8ecf1);
        }
        QScrollBar:vertical {
            background: #edf2f7; width: 10px; border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #cbd5e0; border-radius: 5px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #a0aec0; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    """

def dialog_style() -> str:
    return """
        QDialog { background-color: #ffffff; }
        QLabel  { color: #111827; font-family: 'Segoe UI'; }
        QLineEdit, QTimeEdit, QDateEdit {
            background-color: #f9fafb; border: 1px solid #e5e7eb;
            border-radius: 8px; padding: 8px 12px;
            font-family: 'Segoe UI'; font-size: 11pt; color: #111827;
        }
        QLineEdit:focus, QTimeEdit:focus, QDateEdit:focus { border: 1px solid #2563eb; }
    """

def spinbox_style() -> str:
    return """
        QSpinBox {
            background-color: #f9fafb; border: 1px solid #e5e7eb;
            border-radius: 8px; padding: 8px 12px;
            font-family: 'Segoe UI'; font-size: 11pt; color: #111827;
        }
        QSpinBox:focus { border: 1px solid #2563eb; }
    """

def dialog_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont(_conf.font, 14, QFont.Bold))
    lbl.setStyleSheet("color: #111827; margin-bottom: 8px;")
    return lbl

def info_label(text: str, color: str = "#6b7280", bg: str = "#f3f4f6") -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont(_conf.font, 10))
    lbl.setStyleSheet(f"color: {color}; background-color: {bg}; border-radius: 8px; padding: 10px;")
    lbl.setWordWrap(True)
    return lbl

def warning_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont(_conf.font, 9))
    lbl.setStyleSheet("""
        color: #dc2626; background-color: #fef2f2;
        border: 1px solid #fecaca; border-radius: 8px; padding: 8px;
    """)
    lbl.setWordWrap(True)
    return lbl

def cancel_button() -> QPushButton:
    btn = QPushButton("Abbrechen")
    btn.setMinimumHeight(42)
    btn.setFont(QFont(_conf.font, 11))
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton { background-color: #f3f4f6; color: #1f2937;
                      border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px 20px; }
        QPushButton:hover { background-color: #e5e7eb; }
    """)
    return btn

def primary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setMinimumHeight(42)
    btn.setFont(QFont(_conf.font, 11, QFont.Bold))
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton { background-color: #2563eb; color: white;
                      border: none; border-radius: 8px; padding: 10px 20px; }
        QPushButton:hover    { background-color: #1d4ed8; }
        QPushButton:pressed  { background-color: #1e40af; }
        QPushButton:disabled { background-color: #9ca3af; }
    """)
    return btn
