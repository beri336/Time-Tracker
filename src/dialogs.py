import time
from datetime import datetime
import sqlite3

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDateEdit, QTimeEdit,
    QSpinBox, QHBoxLayout, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractSpinBox
)

from .styles import dialog_style, spinbox_style, dialog_title, info_label, warning_label, cancel_button, primary_button
from .db import insert_entry, all_entries, month_and_week_stats

from .config import Config as _conf


class ManualEntryDialog(QDialog):
    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Manueller Eintrag")
        self.setMinimumWidth(400)
        self.setStyleSheet(dialog_style())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(dialog_title("Manueller Eintrag"))

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.date_input.setMinimumHeight(40)
        self.date_input.setStyleSheet("""
            QDateEdit::drop-down {
                width: 0px;
                border: none;
            }
        """)

        self.start_input = QTimeEdit()
        self.start_input.setDisplayFormat("HH:mm:ss")
        self.start_input.setMinimumHeight(40)
        self.start_input.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.end_input = QTimeEdit(QTime.currentTime())
        self.end_input.setDisplayFormat("HH:mm:ss")
        self.end_input.setMinimumHeight(40)
        self.end_input.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.pause_input = QSpinBox()
        self.pause_input.setMinimum(0)
        self.pause_input.setMaximum(480)
        self.pause_input.setSuffix(" min")
        self.pause_input.setMinimumHeight(40)
        self.pause_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.pause_input.setStyleSheet(spinbox_style())

        for text, widget in [
            ("Datum", self.date_input),
            ("Anfangszeit", self.start_input),
            ("Endzeit", self.end_input),
            ("Pause (in Minuten)", self.pause_input),
        ]:
            lbl = QLabel(text)
            lbl.setFont(QFont(_conf.font, 10, QFont.Bold))
            layout.addWidget(lbl)
            layout.addWidget(widget)

        btn_layout = QHBoxLayout()
        btn_cancel = cancel_button()
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = primary_button("Speichern")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        if self.start_input.time() >= self.end_input.time():
            QMessageBox.warning(self, 
                                "Ungültige Zeiten", 
                                "Die Endzeit muss nach der Anfangszeit liegen.")
            return
        start_secs = self.start_input.time().msecsSinceStartOfDay() // 1000
        end_secs   = self.end_input.time().msecsSinceStartOfDay() // 1000
        net_secs   = max(0, end_secs - start_secs - self.pause_input.value() * 60)

        insert_entry(
            self.db_path,
            self.date_input.date().toString("dd.MM.yyyy"),
            self.start_input.time().toString("HH:mm:ss"),
            self.end_input.time().toString("HH:mm:ss"),
            time.strftime("%H:%M:%S", time.gmtime(net_secs)),
        )
        self.accept()

class StartTimeDialog(QDialog):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setWindowTitle("Anfangszeit nachtragen")
        self.setMinimumWidth(380)
        self.setStyleSheet(dialog_style())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(dialog_title("Vergessene Anfangszeit nachtragen"))
        today_str = datetime.now().strftime("%d.%m.%Y")
        layout.addWidget(info_label(
            "Der Timer wird rückwirkend für heute ({x}) gestartet.\nDie Endzeit wird beim Stoppen des Timers gesetzt.".replace("{x}", f"{today_str}")
        ))

        start_label = QLabel("Wann hast du angefangen?")
        start_label.setFont(QFont(_conf.font, 10, QFont.Bold))
        layout.addWidget(start_label)

        self.start_input = QTimeEdit(QTime.currentTime())
        self.start_input.setDisplayFormat("HH:mm:ss")
        self.start_input.setMinimumHeight(42)
        self.start_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        layout.addWidget(self.start_input)

        self.warn = QLabel("⚠️ Die Anfangszeit darf nicht in der Zukunft liegen.")
        self.warn.setFont(QFont(_conf.font, 9))
        self.warn.setStyleSheet("color: #dc2626; padding: 4px;")
        self.warn.setVisible(False)
        layout.addWidget(self.warn)

        self.start_input.timeChanged.connect(
            lambda: self.warn.setVisible(self.start_input.time() > QTime.currentTime())
        )

        btn_layout = QHBoxLayout()
        btn_cancel = cancel_button()
        btn_cancel.clicked.connect(self.reject)
        btn_start = primary_button("Timer starten")
        btn_start.clicked.connect(self._apply_start)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_start)
        layout.addLayout(btn_layout)

    def _apply_start(self):
        selected = self.start_input.time()
        if selected > QTime.currentTime():
            QMessageBox.warning(self, 
                                "Ungültige Zeiten", 
                                "Die Anfangszeit darf nicht in der Zukunft liegen.")
            return
        if self.parent_window.running:
            QMessageBox.warning(self, 
                                "Timer läuft bereits", 
                                "Stoppe zuerst den aktuellen Timer.")
            return
        now_secs   = QTime.currentTime().msecsSinceStartOfDay() // 1000
        start_secs = selected.msecsSinceStartOfDay() // 1000
        
        self.parent_window.session_start = selected.toString("HH:mm:ss")
        self.parent_window.elapsed_time  = 0
        self.parent_window.start_time    = time.time() - (now_secs - start_secs)
        self.parent_window.running = True
        self.parent_window.status_label.setText("⏱  Läuft ...")
        self.parent_window._set_button_states(start=False, pause=True, cont=False, stop=True)
        self.accept()

class EndTimeDialog(QDialog):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setWindowTitle("Endzeit nachtragen")
        self.setMinimumWidth(380)
        self.setStyleSheet(dialog_style())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(dialog_title("Vergessene Endzeit nachtragen"))
        layout.addWidget(info_label("Der Timer wird mit der eingetragenen Endzeit gestoppt\nund der Eintrag in der Datenbank gespeichert."))

        if not self.parent_window.running:
            layout.addWidget(warning_label("⚠️ Der Timer läuft aktuell nicht. Starte zuerst den Timer."))
        else:
            layout.addWidget(info_label(
                "⏱ Timer gestartet um: {x}".replace("{x}", self.parent_window.session_start),
                color="#2563eb", bg="#eff6ff",
            ))

        end_label = QLabel("Wann hast du aufgehört?")
        end_label.setFont(QFont(_conf.font, 10, QFont.Bold))
        layout.addWidget(end_label)

        self.end_input = QTimeEdit(QTime.currentTime())
        self.end_input.setDisplayFormat("HH:mm:ss")
        self.end_input.setMinimumHeight(42)
        self.end_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        layout.addWidget(self.end_input)

        self.warn = QLabel()
        self.warn.setFont(QFont(_conf.font, 9))
        self.warn.setStyleSheet("color: #dc2626; padding: 4px;")
        self.warn.setVisible(False)
        self.warn.setWordWrap(True)
        layout.addWidget(self.warn)

        self.end_input.timeChanged.connect(self._check_end)

        btn_layout = QHBoxLayout()
        btn_cancel = cancel_button()
        btn_cancel.clicked.connect(self.reject)
        self.btn_stop = primary_button("Timer stoppen und speichern")
        self.btn_stop.setEnabled(self.parent_window.running)
        self.btn_stop.clicked.connect(self._apply_end)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

    def _check_end(self):
        sel = self.end_input.time()
        if sel > QTime.currentTime():
            self.warn.setText("⚠️ Die Endzeit darf nicht in der Zukunft liegen.")
            self.warn.setVisible(True)
            return
        if self.parent_window.running and self.parent_window.session_start:
            if sel <= QTime.fromString(self.parent_window.session_start, "HH:mm:ss"):
                self.warn.setText("⚠️ Die Endzeit muss nach der Anfangszeit liegen.")
                self.warn.setVisible(True)
                return
        self.warn.setVisible(False)

    def _apply_end(self):
        sel = self.end_input.time()
        if sel > QTime.currentTime():
            QMessageBox.warning(self, 
                                "Ungültige Zeit", 
                                "Die Endzeit darf nicht in der Zukunft liegen.")
            return
        t_start = QTime.fromString(self.parent_window.session_start, "HH:mm:ss")
        if sel <= t_start:
            QMessageBox.warning(self, 
                                "Ungültige Zeit", 
                                "Die Endzeit muss nach der Anfangszeit liegen.")
            return
        start_secs = t_start.msecsSinceStartOfDay() // 1000
        end_secs   = sel.msecsSinceStartOfDay() // 1000
        net_secs   = max(0, end_secs - start_secs)
        import time as _time
        self.parent_window.session_end  = sel.toString("HH:mm:ss")
        self.parent_window.elapsed_time = net_secs
        self.parent_window.running = False

        insert_entry(
            self.parent_window.database_path,
            datetime.now().strftime("%d.%m.%Y"),
            self.parent_window.session_start,
            self.parent_window.session_end,
            _time.strftime("%H:%M:%S", _time.gmtime(net_secs)),
        )
        self.parent_window._reset_timer()
        self.parent_window.update_summary()
        self.parent_window.status_label.setText("Bereit zum Starten3")
        self.parent_window._set_button_states(start=True, pause=False, cont=False, stop=False)
        self.accept()

class AllEntriesDialog(QDialog):
    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Alle Einträge")
        self.setMinimumSize(700, 500)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel  { color: #111827; font-family: 'Segoe UI'; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: #f3f4f6;
                font-family: 'Segoe UI'; font-size: 10pt;
            }
            QTableWidget::item { padding: 8px; color: #111827; }
            QTableWidget::item:selected { background-color: #eff6ff; color: #2563eb; }
            QHeaderView::section {
                background-color: #f9fafb; color: #6b7280;
                font-weight: bold; font-family: 'Segoe UI'; font-size: 10pt;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }
            QPushButton {
                background-color: #f3f4f6; color: #1f2937;
                border: 1px solid #e5e7eb; border-radius: 8px;
                padding: 8px 16px; font-family: 'Segoe UI'; font-size: 10pt;
            }
            QPushButton:hover { background-color: #e5e7eb; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Alle Datenbankeinträge")
        title.setFont(QFont(_conf.font, 14, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setFont(QFont(_conf.font, 10))
        self.count_lbl.setStyleSheet(
            "color: #2563eb; background-color: #eff6ff; border-radius: 8px; padding: 4px 10px;"
        )
        header_layout.addWidget(self.count_lbl)
        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", 
                                              "Datum", 
                                              "Anfangszeit",
                                              "Endzeit",
                                              "Dauer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self._load_data()

        btn_layout = QHBoxLayout()
        btn_delete = QPushButton("🗑  Eintrag löschen")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("""
            QPushButton { background-color: #fef2f2; color: #dc2626;
                          border: 1px solid #fecaca; border-radius: 8px; padding: 8px 16px; }
            QPushButton:hover { background-color: #fee2e2; }
            QPushButton:disabled { background-color: #f9fafb; color: #9ca3af; border-color: #e5e7eb; }
        """)

        btn_delete.clicked.connect(self._delete_entry)

        btn_close = QPushButton("Schließen")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _load_data(self):
        rows = all_entries(self.db_path)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"{len(rows)} Einträge")

    def _delete_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, 
                                    "Kein Eintrag gewählt", 
                                    "Bitte wähle zuerst einen Eintrag aus.")
            return
        entry_id   = self.table.item(row, 0).text()
        entry_date = self.table.item(row, 1).text()
        
        if QMessageBox.question(
            self, "Eintrag löschen",
            "Eintrag vom {x} (ID: {y}) wirklich löschen?".format(x=entry_date, y=entry_id),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM work_time WHERE id = ?", (entry_id,))
            conn.commit()
            conn.close()
            self._load_data()

class StatisticsDialog(QDialog):
    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Monats- und Wochenübersicht")
        self.setMinimumSize(650, 480)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel  { color: #111827; font-family: 'Segoe UI'; }
            QTableWidget {
                background-color: #ffffff; border: 1px solid #e5e7eb;
                border-radius: 8px; gridline-color: #f3f4f6;
                font-family: 'Segoe UI'; font-size: 10pt;
            }
            QTableWidget::item { padding: 8px; color: #111827; }
            QHeaderView::section {
                background-color: #f9fafb; color: #6b7280; font-weight: bold;
                padding: 8px; border: none; border-bottom: 1px solid #e5e7eb;
            }
            QPushButton {
                background-color: #f3f4f6; color: #1f2937;
                border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #e5e7eb; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📊 Monats- und Wochenübersicht")
        title.setFont(QFont(_conf.font, 14, QFont.Bold))
        layout.addWidget(title)

        month_title = QLabel("Monatsübersicht")
        month_title.setFont(QFont(_conf.font, 11, QFont.Bold))
        month_title.setStyleSheet("color: #2563eb;")
        layout.addWidget(month_title)

        self.month_table = QTableWidget()
        self.month_table.setColumnCount(3)
        self.month_table.setHorizontalHeaderLabels(["Monat", 
                                                    "Sessions", 
                                                    "Gesamtzeit"])
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.month_table.verticalHeader().setVisible(False)
        self.month_table.setAlternatingRowColors(True)
        layout.addWidget(self.month_table)

        week_title = QLabel("Wochenübersicht")
        week_title.setFont(QFont(_conf.font, 11, QFont.Bold))
        week_title.setStyleSheet("color: #2563eb;")
        layout.addWidget(week_title)

        self.week_table = QTableWidget()
        self.week_table.setColumnCount(3)
        self.week_table.setHorizontalHeaderLabels(["Woche", 
                                                   "Sessions", 
                                                   "Gesamtzeit"])
        self.week_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.week_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.week_table.verticalHeader().setVisible(False)
        self.week_table.setAlternatingRowColors(True)
        layout.addWidget(self.week_table)

        self._load_stats()

        btn_close = QPushButton("Schließen")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def _load_stats(self):
        month_rows, week_rows = month_and_week_stats(self.db_path)

        self.month_table.setRowCount(len(month_rows))
        for r, row in enumerate(month_rows):
            total = time.strftime("%H:%M:%S", time.gmtime(row[2] or 0))
            for c, val in enumerate([row[0], str(row[1]), total]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.month_table.setItem(r, c, item)

        self.week_table.setRowCount(len(week_rows))
        for r, row in enumerate(week_rows):
            total = time.strftime("%H:%M:%S", time.gmtime(row[2] or 0))
            for c, val in enumerate([row[0], str(row[1]), total]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.week_table.setItem(r, c, item)
