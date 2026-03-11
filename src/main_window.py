import os
import sys
import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QSizePolicy, QFrame, QPushButton,
    QFileDialog, QMessageBox,
)

from .styles import ModernButton, ButtonStyle, main_window_style
from .db import (
    ensure_database, change_database, clone_database, new_database,
    summary_by_date, export_csv, import_csv, export_json,
)
from .dialogs import ManualEntryDialog, StartTimeDialog, EndTimeDialog, AllEntriesDialog, StatisticsDialog

from .config import Config as _conf


class WorkTimeTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_conf.lbl_title)
        self.setMinimumSize(700, 1000)

        self.start_time: float | None = None
        self.elapsed_time: float = 0
        self.running: bool = False
        self.session_start: str = ""
        self.session_end: str = ""

        self.database_folder = os.getcwd()
        self.database_path   = ensure_database(self.database_folder)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        layout.addWidget(self._create_header())
        layout.addWidget(self._create_timer_card())
        layout.addLayout(self._create_button_layout())
        layout.addLayout(self._create_button_2_layout())
        layout.addWidget(self._create_summary_card())
        layout.addLayout(self._create_actions_layout())
        layout.addLayout(self._create_actions_2_layout())
        layout.addLayout(self._create_database_layout())
        layout.addStretch()

        self.db_path_label.setText(self._format_path(self.database_path))
        self.update_summary()
        self._apply_styles()
        self._setup_menu()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _create_header(self) -> QLabel:
        lbl = QLabel(_conf.lbl_title)
        lbl.setFont(QFont(_conf.font, 24, QFont.Bold))
        lbl.setStyleSheet("color: #111827; margin-bottom: 10px;")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _create_timer_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
                padding: 30px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(10, 0, 10, 0)
        self.status_label = QLabel(_conf.lbl_status)
        self.status_label.setFont(QFont(_conf.font, 15, QFont.Bold))
        self.status_label.setStyleSheet("""
            color: #6b7280; margin-bottom: 20px;
            background-color: #e0e7ff;
            border-radius: 12px; padding: 10px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        wrapper.addWidget(self.status_label)
        layout.addLayout(wrapper)

        self.time_label = QLabel(_conf.lbl_time)
        self.time_label.setFont(QFont(_conf.font, 56, QFont.Bold))
        self.time_label.setStyleSheet("""
            color: #2563eb; margin: 10px 0;
            background-color: #e0e7ff;
            border-radius: 12px; padding: 20px;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        return card

    def _create_button_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.btn_start = ModernButton("▶  Start", primary=True)
        self.btn_start.clicked.connect(self.start_timer)

        self.btn_pause = ModernButton("⏸  Pause")
        self.btn_pause.clicked.connect(self.pause_timer)
        self.btn_pause.setEnabled(False)

        self.btn_continue = ModernButton("▶  Weiter", primary=True)
        self.btn_continue.clicked.connect(self.continue_timer)
        self.btn_continue.setEnabled(False)

        self.btn_stop = ModernButton("⏹  Stop")
        self.btn_stop.clicked.connect(self.stop_timer)
        self.btn_stop.setEnabled(False)

        for btn in (self.btn_start, self.btn_pause, self.btn_continue, self.btn_stop):
            layout.addWidget(btn)
        return layout

    def _create_button_2_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.man_entry_button = QPushButton("Manueller Eintrag")
        ButtonStyle.layout_button_style(self.man_entry_button)
        self.man_entry_button.clicked.connect(self.setup_man_entry)

        self.btn_start_time = QPushButton("Anfangszeit nachtragen")
        ButtonStyle.layout_button_style(self.btn_start_time)
        self.btn_start_time.clicked.connect(self.man_start_time)

        self.btn_end_time = QPushButton("Endzeit nachtragen")
        ButtonStyle.layout_button_style(self.btn_end_time)
        self.btn_end_time.clicked.connect(self.man_end_time)

        for btn in (self.man_entry_button, self.btn_start_time, self.btn_end_time):
            layout.addWidget(btn)
        return layout

    def _create_actions_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.btn_csv_export = QPushButton("CSV Export")
        ButtonStyle.action_button_style(self.btn_csv_export)
        self.btn_csv_export.clicked.connect(self.export_to_csv)

        self.btn_json_exp = QPushButton("JSON Export")
        ButtonStyle.action_button_style(self.btn_json_exp)
        self.btn_json_exp.clicked.connect(self.export_to_json)

        layout.addWidget(self.btn_csv_export)
        layout.addWidget(self.btn_json_exp)
        return layout

    def _create_actions_2_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.btn_csv_import = QPushButton("CSV Import")
        ButtonStyle.action_button_style(self.btn_csv_import)
        self.btn_csv_import.clicked.connect(self.import_from_csv)

        self.btn_all_entries = QPushButton("Alle Einträge anzeigen")
        ButtonStyle.action_button_style(self.btn_all_entries)
        self.btn_all_entries.clicked.connect(self.show_all_entries)

        layout.addWidget(self.btn_csv_import)
        layout.addWidget(self.btn_all_entries)
        return layout

    def _create_summary_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setStyleSheet("""
            QFrame#summaryCard {
                background-color: #f9fafb;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Zusammenfassung")
        title.setFont(QFont(_conf.font, 16, QFont.Bold))
        title.setStyleSheet("color: #111827; margin-bottom: 10px;")
        layout.addWidget(title)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px;
                color: #374151;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.summary_text)
        return card

    def _create_database_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        lbl = QLabel("Datenbank:")
        lbl.setFont(QFont(_conf.font, 10))
        lbl.setStyleSheet("color: #6b7280;")

        self.db_path_label = QLabel("Noch kein Pfad gewählt")
        self.db_path_label.setFont(QFont(_conf.font, 10))
        self.db_path_label.setStyleSheet("color: #2563eb;")
        self.db_path_label.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(self.db_path_label, 1)
        return layout

    def _setup_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("&Datei")
        self._add_action(file_menu, "Als CSV exportieren", self.export_to_csv)
        self._add_action(file_menu, "Als JSON exportieren", self.export_to_json)
        file_menu.addSeparator()
        self._add_action(file_menu, "CSV importieren", self.import_from_csv)
        file_menu.addSeparator()
        self._add_action(file_menu, "Datenbank-Speicherort ändern", self.change_database_folder)
        self._add_action(file_menu, "Datenbank klonen", self.clone_database_ui)
        self._add_action(file_menu, "Neue Datenbank erstellen", self.create_new_database_ui)

        edit_menu = mb.addMenu("&Bearbeiten")
        self._add_action(edit_menu, "Manueller Eintrag", self.setup_man_entry)
        self._add_action(edit_menu, "Vergessene Anfangszeit nachtragen", self.man_start_time)
        self._add_action(edit_menu, "Vergessene Endzeit nachtragen", self.man_end_time)

        view_menu = mb.addMenu("&Ansicht")
        self._add_action(view_menu, "Alle Datenbankeinträge anzeigen", self.show_all_entries)

        stats_menu = mb.addMenu("&Statistik")
        self._add_action(stats_menu, "Monats- und Wochenübersicht", self.show_statistics)

    @staticmethod
    def _add_action(menu, label: str, slot):
        action = QAction(label)
        action.triggered.connect(slot)
        menu.addAction(action)

    def change_database_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Datenbank-Speicherort wählen")
        if folder:
            self.database_folder = folder
            self.database_path   = ensure_database(folder)
            self.db_path_label.setText(self._format_path(self.database_path))
            self.update_summary()

    def clone_database_ui(self):
        if not os.path.exists(self.database_path):
            QMessageBox.warning(self, "Keine Datenbank", "Es gibt noch keine Datenbank zum Klonen.")
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Datenbank klonen nach", "work_time_backup.db", "SQLite Datenbank (*.db)"
        )
        if dest:
            clone_database(self.database_path, dest)
            QMessageBox.information(self, "Geklont", f"Datenbank wurde kopiert nach:\n{dest}")

    def create_new_database_ui(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "Neue Datenbank erstellen", "work_time.db", "SQLite Datenbank (*.db)"
        )
        if dest:
            self.database_folder = os.path.dirname(dest)
            self.database_path   = dest
            self.db_path_label.setText(self._format_path(dest))
            new_database(dest)
            self.update_summary()
            QMessageBox.information(self, "Erstellt", f"Neue Datenbank erstellt:\n{dest}")

    def update_summary(self):
        rows = summary_by_date(self.database_path)
        if not rows:
            self.summary_text.setHtml("<i>Noch keine Einträge vorhanden.</i>")
            return
        html = "<div style='font-family: Segoe UI;'>"
        for row in rows:
            total = row["total_str"]
            html += (
                f"<p style='margin: 5px 0;'>"
                f"<b>📅 {row['date']}</b> — {row['count']} Session(s) — "
                f"<span style='color:#2563eb;'>{total}</span></p>"
            )
        html += "</div>"
        self.summary_text.setHtml(html)

    def _update_clock(self):
        if self.running and self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.time_label.setText(time.strftime("%H:%M:%S", time.gmtime(elapsed)))

    def _set_button_states(self, *, start, pause, cont, stop):
        self.btn_start.setEnabled(start)
        self.btn_pause.setEnabled(pause)
        self.btn_continue.setEnabled(cont)
        self.btn_stop.setEnabled(stop)

    def start_timer(self):
        if not self.running:
            self.start_time    = time.time()
            self.elapsed_time  = 0
            self.session_start = datetime.now().strftime("%H:%M:%S")
            self.running = True
            self.status_label.setText("⏱  Läuft ...")
            self._set_button_states(start=False, pause=True, cont=False, stop=True)

    def pause_timer(self):
        if self.running and self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time
            self.running = False
            self.status_label.setText("⏸  Pausiert")
            self._set_button_states(start=False, pause=False, cont=True, stop=True)

    def continue_timer(self):
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.status_label.setText("⏱  Läuft ...")
            self._set_button_states(start=False, pause=True, cont=False, stop=True)

    def stop_timer(self):
        if self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time
            self.session_end  = datetime.now().strftime("%H:%M:%S")
            self.running = False
            from .db import insert_entry
            insert_entry(
                self.database_path,
                datetime.now().strftime("%d.%m.%Y"),
                self.session_start,
                self.session_end,
                time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time)),
            )
            self._reset_timer()
            self.status_label.setText(_conf.lbl_status)
            self._set_button_states(start=True, pause=False, cont=False, stop=False)
            self.update_summary()

    def _reset_timer(self):
        self.start_time   = None
        self.elapsed_time = 0
        self.time_label.setText(_conf.lbl_time)

    def setup_man_entry(self):
        dlg = ManualEntryDialog(self.database_path, self)
        if dlg.exec():
            self.update_summary()

    def man_start_time(self):
        dlg = StartTimeDialog(self, self)
        dlg.exec()

    def man_end_time(self):
        dlg = EndTimeDialog(self, self)
        dlg.exec()

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Als CSV exportieren", "", "CSV-Dateien (*.csv)"
        )
        if not path:
            return
        count = export_csv(self.database_path, path)
        QMessageBox.information(
            self, "Export erfolgreich", f"✅ {count} Einträge exportiert nach:\n{path}"
        )

    def import_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "CSV importieren", "", "CSV-Dateien (*.csv)"
        )
        if not path:
            return
        try:
            imported, errors = import_csv(self.database_path, path)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"CSV konnte nicht gelesen werden:\n{e}")
            return
        self.update_summary()
        msg = f"✅ {imported} Einträge importiert."
        if errors:
            msg += f"\n⚠️ {errors} Zeile(n) übersprungen (ungültiges Format)."
        QMessageBox.information(self, "Import abgeschlossen", msg)

    def export_to_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Als JSON exportieren", "", "JSON-Dateien (*.json)"
        )
        if not path:
            return
        count = export_json(self.database_path, path)
        QMessageBox.information(
            self, "Export erfolgreich", f"✅ {count} Einträge exportiert nach:\n{path}"
        )

    def show_all_entries(self):
        dlg = AllEntriesDialog(self.database_path, self)
        dlg.exec()
        self.update_summary()

    def show_statistics(self):
        dlg = StatisticsDialog(self.database_path, self)
        dlg.exec()

    def _apply_styles(self):
        self.setStyleSheet(main_window_style())

    @staticmethod
    def _format_path(path: str) -> str:
        if len(path) > 60:
            head, tail = os.path.split(path)
            return f"...{head[-30:]}/{tail}"
        return path
