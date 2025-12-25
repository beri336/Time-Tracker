# app.py
import sys
import time
from datetime import datetime
import os
import sqlite3
import csv
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFrame, 
                               QFileDialog, QMessageBox, QScrollArea)
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPainterPath


class RoundedFrame(QFrame):
    """Custom frame with rounded corners and shadow effect"""
    def __init__(self, parent=None, radius=12):
        super().__init__(parent)
        self.radius = radius
        self.setAutoFillBackground(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(2, 2, -2, -2), self.radius, self.radius)
        
        painter.fillPath(path, self.palette().window())
        painter.end()


class AnimatedButton(QPushButton):
    """Button with hover animation"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._scale = 1.0
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def get_scale(self):
        return self._scale
    
    def set_scale(self, scale):
        self._scale = scale
        self.update()
        
    scale = Property(float, get_scale, set_scale)
    
    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self._scale)
        self.animation.setEndValue(1.05)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self._scale)
        self.animation.setEndValue(1.0)
        self.animation.start()
        super().leaveEvent(event)


class WorkTimeTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Work Time Tracker")
        self.setMinimumSize(700, 600)
        
        # Timer variables
        self.start_time = None
        self.elapsed_time = 0
        self.running = False
        self.database_folder = os.getcwd()
        self.database_path = os.path.join(self.database_folder, "work_time.db")
        self.reminder_interval = 60 * 60
        self.last_reminder_time = None
        
        # Initialize database
        self.init_database()
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
        # Setup timers
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
    def setup_ui(self):
        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Work Time Tracker")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        main_layout.addWidget(title)
        
        # Time display card
        time_card = RoundedFrame(radius=16)
        time_card.setObjectName("timeCard")
        time_card_layout = QVBoxLayout(time_card)
        time_card_layout.setContentsMargins(30, 25, 30, 25)
        
        time_label_title = QLabel("Current Time")
        time_label_title.setAlignment(Qt.AlignCenter)
        time_label_title.setFont(QFont("Segoe UI", 14))
        time_label_title.setObjectName("timeTitle")
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Segoe UI", 56, QFont.Bold))
        self.time_label.setObjectName("timeDisplay")
        
        time_card_layout.addWidget(time_label_title)
        time_card_layout.addWidget(self.time_label)
        main_layout.addWidget(time_card)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.start_button = AnimatedButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = AnimatedButton("Pause")
        self.pause_button.setObjectName("pauseButton")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        
        self.continue_button = AnimatedButton("Continue")
        self.continue_button.setObjectName("continueButton")
        self.continue_button.clicked.connect(self.continue_timer)
        self.continue_button.setEnabled(False)
        
        self.stop_button = AnimatedButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_timer)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.continue_button)
        buttons_layout.addWidget(self.stop_button)
        main_layout.addLayout(buttons_layout)
        
        # Export button
        self.export_button = AnimatedButton("Export to CSV")
        self.export_button.setObjectName("exportButton")
        self.export_button.clicked.connect(self.export_to_csv)
        main_layout.addWidget(self.export_button)
        
        # Summary dashboard
        summary_card = RoundedFrame(radius=16)
        summary_card.setObjectName("summaryCard")
        summary_card_layout = QVBoxLayout(summary_card)
        summary_card_layout.setContentsMargins(20, 20, 20, 20)
        
        summary_title = QLabel("Summary Dashboard")
        summary_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        summary_title.setObjectName("summaryTitle")
        summary_card_layout.addWidget(summary_title)
        
        # Scrollable summary content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setObjectName("summaryScroll")
        
        self.summary_content = QLabel("")
        self.summary_content.setFont(QFont("Segoe UI", 11))
        self.summary_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_content.setWordWrap(True)
        self.summary_content.setObjectName("summaryContent")
        
        scroll_area.setWidget(self.summary_content)
        summary_card_layout.addWidget(scroll_area)
        main_layout.addWidget(summary_card)
        
        # Database path
        db_layout = QHBoxLayout()
        db_layout.setSpacing(12)
        
        self.change_db_button = AnimatedButton("Choose Database Folder")
        self.change_db_button.setObjectName("dbButton")
        self.change_db_button.clicked.connect(self.change_database_folder)
        
        self.db_path_label = QLabel(self.format_path(self.database_path))
        self.db_path_label.setFont(QFont("Segoe UI", 10))
        self.db_path_label.setObjectName("dbPath")
        
        db_layout.addWidget(self.change_db_button)
        db_layout.addWidget(self.db_path_label, 1)
        main_layout.addLayout(db_layout)
        
        self.update_summary()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f5f7fa, stop:1 #e8ecf1);
            }
            
            QLabel {
                color: #2c3e50;
            }
            
            #timeCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #667eea, stop:1 #764ba2);
                border-radius: 16px;
            }
            
            #timeTitle {
                color: #ffffff;
                font-weight: 500;
            }
            
            #timeDisplay {
                color: #ffffff;
                font-weight: 700;
                letter-spacing: 2px;
            }
            
            AnimatedButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }
            
            AnimatedButton:hover {
                background-color: #5568d3;
            }
            
            AnimatedButton:pressed {
                background-color: #4c5fc7;
            }
            
            AnimatedButton:disabled {
                background-color: #cbd5e0;
                color: #a0aec0;
            }
            
            #startButton {
                background-color: #48bb78;
            }
            
            #startButton:hover {
                background-color: #38a169;
            }
            
            #pauseButton {
                background-color: #ed8936;
            }
            
            #pauseButton:hover {
                background-color: #dd6b20;
            }
            
            #stopButton {
                background-color: #f56565;
            }
            
            #stopButton:hover {
                background-color: #e53e3e;
            }
            
            #continueButton {
                background-color: #4299e1;
            }
            
            #continueButton:hover {
                background-color: #3182ce;
            }
            
            #exportButton {
                background-color: #9f7aea;
            }
            
            #exportButton:hover {
                background-color: #805ad5;
            }
            
            #summaryCard {
                background-color: white;
                border-radius: 16px;
            }
            
            #summaryTitle {
                color: #2d3748;
            }
            
            #summaryContent {
                color: #4a5568;
                padding: 10px;
            }
            
            #summaryScroll {
                background: transparent;
                border: none;
            }
            
            #dbButton {
                background-color: #718096;
                min-width: 200px;
            }
            
            #dbButton:hover {
                background-color: #4a5568;
            }
            
            #dbPath {
                color: #718096;
            }
            
            QScrollBar:vertical {
                background: #edf2f7;
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: #cbd5e0;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0aec0;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def init_database(self):
        if not os.path.exists(self.database_folder):
            os.makedirs(self.database_folder)
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS work_time (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            start_time TEXT NOT NULL,
                            end_time TEXT NOT NULL,
                            duration TEXT NOT NULL
                        )''')
        conn.commit()
        conn.close()
    
    def start_timer(self):
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.session_start = datetime.now().strftime("%H:%M:%S")
            self.running = True
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.continue_button.setEnabled(False)
            self.last_reminder_time = time.time()
    
    def pause_timer(self):
        if self.running:
            self.elapsed_time = time.time() - self.start_time
            self.running = False
            self.pause_button.setEnabled(False)
            self.continue_button.setEnabled(True)
    
    def continue_timer(self):
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.pause_button.setEnabled(True)
            self.continue_button.setEnabled(False)
            self.last_reminder_time = time.time()
    
    def stop_timer(self):
        if self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time
            self.session_end = datetime.now().strftime("%H:%M:%S")
            self.running = False
            self.save_time()
            self.reset_timer()
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.continue_button.setEnabled(False)
            self.stop_button.setEnabled(False)
    
    def reset_timer(self):
        self.start_time = None
        self.elapsed_time = 0
        self.time_label.setText("00:00:00")
    
    def update_clock(self):
        if self.running:
            elapsed = time.time() - self.start_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.time_label.setText(formatted_time)
            
            if self.last_reminder_time and (time.time() - self.last_reminder_time) >= self.reminder_interval:
                self.send_reminder()
                self.last_reminder_time = time.time()
    
    def send_reminder(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Reminder")
        msg.setText("You have been working for a while. Consider taking a short break!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def save_time(self):
        current_date = datetime.now().strftime("%d.%m.%Y")
        work_duration = time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time))
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO work_time (date, start_time, end_time, duration) 
                          VALUES (?, ?, ?, ?)''', (current_date, self.session_start, self.session_end, work_duration))
        conn.commit()
        conn.close()
        self.update_summary()
    
    def change_database_folder(self):
        new_folder = QFileDialog.getExistingDirectory(self, "Choose Database Folder")
        if new_folder:
            self.database_folder = new_folder
            self.database_path = os.path.join(self.database_folder, "work_time.db")
            self.db_path_label.setText(self.format_path(self.database_path))
            self.init_database()
            self.update_summary()
    
    def format_path(self, path):
        if len(path) > 50:
            head, tail = os.path.split(path)
            return f".../{head[-25:]}/{tail}"
        return path
    
    def export_to_csv(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export to CSV", 
            "", 
            "CSV files (*.csv)"
        )
        if save_path:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT date, start_time, end_time, duration FROM work_time''')
            rows = cursor.fetchall()
            conn.close()
            
            with open(save_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Start Time", "End Time", "Duration"])
                writer.writerows(rows)
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Success")
            msg.setText(f"Data exported to {save_path}")
            msg.exec()
    
    def update_summary(self):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT date, COUNT(*), SUM(strftime('%s', duration) - strftime('%s', '00:00:00')) 
                          FROM work_time GROUP BY date ORDER BY date DESC''')
        rows = cursor.fetchall()
        conn.close()
        
        summary_text = ""
        for row in rows:
            total_duration = time.strftime("%H:%M:%S", time.gmtime(row[2] if row[2] else 0))
            summary_text += f"<b>📅 {row[0]}</b><br>"
            summary_text += f"&nbsp;&nbsp;&nbsp;Sessions: {row[1]}<br>"
            summary_text += f"&nbsp;&nbsp;&nbsp;Total Time: {total_duration}<br><br>"
        
        if not summary_text:
            summary_text = "<i>No work sessions recorded yet.</i>"
        
        self.summary_content.setText(summary_text)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    tracker = WorkTimeTracker()
    tracker.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
