# app.py

import customtkinter as ctk
import time
from datetime import datetime
import os
import sqlite3
from tkinter import filedialog

class WorkTimeTracker:
    def __init__(self, root):
        # GUI
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        self.root = root
        self.root.title("Work Time Tracker")
        self.root.geometry("600x280")

        self.start_time = None
        self.elapsed_time = 0
        self.running = False
        self.database_folder = os.getcwd()
        self.database_path = os.path.join(self.database_folder, "work_time.db")

        # database init
        self.init_database()

        # central frame
        self.center_frame = ctk.CTkFrame(self.root)
        self.center_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # time label
        self.time_label_frame = ctk.CTkFrame(self.center_frame, fg_color="lightgray", corner_radius=10)
        self.time_label_frame.pack(pady=(0, 30), padx=10, fill="x")

        self.time_label_title = ctk.CTkLabel(self.time_label_frame, text="Current Time", font=("Helvetica", 14, "bold"), text_color="black")
        self.time_label_title.pack(pady=5)

        self.time_label = ctk.CTkLabel(self.time_label_frame, text="00:00:00", font=("Helvetica", 45, "bold"), text_color="blue")
        self.time_label.pack()

        # buttons frame
        self.buttons_frame = ctk.CTkFrame(self.center_frame)
        self.buttons_frame.pack(fill="x")

        # buttons with styling
        button_style = {"font": ("Helvetica", 14)}

        self.start_button = ctk.CTkButton(self.buttons_frame, text="Start", command=self.start_timer, **button_style)
        self.start_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.pause_button = ctk.CTkButton(self.buttons_frame, text="Pause", command=self.pause_timer, state="disabled", **button_style)
        self.pause_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.continue_button = ctk.CTkButton(self.buttons_frame, text="Weiter", command=self.continue_timer, state="disabled", **button_style)
        self.continue_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(self.buttons_frame, text="Stop", command=self.stop_timer, state="disabled", **button_style)
        self.stop_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # changing database path via button
        self.change_db_frame = ctk.CTkFrame(self.center_frame)
        self.change_db_frame.pack(pady=(20, 0))

        self.change_db_button = ctk.CTkButton(self.change_db_frame, text="Choose Database folder", command=self.change_database_folder)
        self.change_db_button.pack(side="left", padx=10, pady=5)

        self.db_path_label = ctk.CTkLabel(self.change_db_frame, text=self.database_path, font=("Helvetica", 12), text_color="green", anchor="w")
        self.db_path_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        # responsive grid settings
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1)

        # start the clock update
        self.update_clock()

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
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            self.continue_button.configure(state="disabled")

    def pause_timer(self):
        if self.running:
            self.elapsed_time = time.time() - self.start_time
            self.running = False
            self.pause_button.configure(state="disabled")
            self.continue_button.configure(state="normal")

    def continue_timer(self):
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.pause_button.configure(state="normal")
            self.continue_button.configure(state="disabled")

    def stop_timer(self):
        if self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time
            self.session_end = datetime.now().strftime("%H:%M:%S")
            self.running = False
            self.save_time()
            self.reset_timer()
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.continue_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")

    def reset_timer(self):
        self.start_time = None
        self.elapsed_time = 0
        self.time_label.configure(text="00:00:00")

    def update_clock(self):
        if self.running:
            elapsed = time.time() - self.start_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.time_label.configure(text=formatted_time)
        self.root.after(1000, self.update_clock)

    def save_time(self):
        current_date = datetime.now().strftime("%d.%m.%Y")
        work_duration = time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time))

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO work_time (date, start_time, end_time, duration) 
                          VALUES (?, ?, ?, ?)''', (current_date, self.session_start, self.session_end, work_duration))
        conn.commit()
        conn.close()

    def change_database_folder(self):
        new_folder = filedialog.askdirectory(title="Datenbankordner auswählen")
        if new_folder:
            self.database_folder = new_folder
            self.database_path = os.path.join(self.database_folder, "time_tracker.db")
            self.db_path_label.configure(text=self.format_path(self.database_path))
            self.init_database()

    def format_path(self, path):
        if len(path) > 50:
            head, tail = os.path.split(path)
            return f".../{head[-25:]}/{tail}"
        return path

# start program
if __name__ == "__main__":
    root = ctk.CTk()
    root.minsize(600,280)
    tracker = WorkTimeTracker(root)

    root.mainloop()