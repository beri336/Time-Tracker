# app.py

import customtkinter as ctk
import time
from datetime import datetime
import os
import sqlite3
import csv
from tkinter import filedialog
from tkinter import messagebox

class WorkTimeTracker:
    def __init__(self, root):
        # GUI
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        self.root = root
        self.root.title("Work Time Tracker")
        self.root.geometry("600x450")

        self.start_time = None
        self.elapsed_time = 0
        self.running = False
        self.database_folder = os.getcwd()
        self.database_path = os.path.join(self.database_folder, "work_time.db")

        # Reminder settings
        self.reminder_interval = 60 * 60 # Default: 1 hour
        self.last_reminder_time = None

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

        self.continue_button = ctk.CTkButton(self.buttons_frame, text="Continue", command=self.continue_timer, state="disabled", **button_style)
        self.continue_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(self.buttons_frame, text="Stop", command=self.stop_timer, state="disabled", **button_style)
        self.stop_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # Export button frame
        self.export_frame = ctk.CTkFrame(self.center_frame)
        self.export_frame.pack(pady=(10, 0))

        self.export_button = ctk.CTkButton(self.export_frame, text="Export to CSV", command=self.export_to_csv, **button_style)
        self.export_button.pack(pady=5)

        # summary dashboard frame
        self.summary_frame = ctk.CTkFrame(self.center_frame)
        self.summary_frame.pack(pady=(20, 0), fill="x")

        self.summary_title = ctk.CTkLabel(self.summary_frame, text="Summary Dashboard", font=("Helvetica", 16, "bold"), text_color="green")
        self.summary_title.pack(pady=5)

        self.summary_content = ctk.CTkLabel(self.summary_frame, text="", font=("Helvetica", 12), text_color="lightgrey")
        self.summary_content.pack(pady=5)

        self.update_summary()

        # changing database path via button
        self.change_db_frame = ctk.CTkFrame(self.center_frame)
        self.change_db_frame.pack(pady=(20, 0))

        self.change_db_button = ctk.CTkButton(self.change_db_frame, text="Choose Database Folder", command=self.change_database_folder)
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
            self.last_reminder_time = time.time()

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
            self.last_reminder_time = time.time()

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

            # Check for reminders
            if self.last_reminder_time and (time.time() - self.last_reminder_time) >= self.reminder_interval:
                self.send_reminder()
                self.last_reminder_time = time.time()

        self.root.after(1000, self.update_clock)

    def send_reminder(self):
        messagebox.showinfo("Reminder", "You have been working for a while. Consider taking a short break!")

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
        new_folder = filedialog.askdirectory(title="Choose Database Folder")
        if new_folder:
            self.database_folder = new_folder
            self.database_path = os.path.join(self.database_folder, "work_time.db")
            self.db_path_label.configure(text=self.format_path(self.database_path))
            self.init_database()

    def format_path(self, path):
        if len(path) > 50:
            head, tail = os.path.split(path)
            return f".../{head[-25:]}/{tail}"
        return path

    def export_to_csv(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Export to CSV")
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

            print(f"Data exported to {save_path}")

    def update_summary(self):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT date, COUNT(*), SUM(strftime('%s', duration) - strftime('%s', '00:00:00')) FROM work_time GROUP BY date''')
        rows = cursor.fetchall()
        conn.close()

        summary_text = ""
        for row in rows:
            total_duration = time.strftime("%H:%M:%S", time.gmtime(row[2]))
            summary_text += f"Date: {row[0]}\nSessions: {row[1]}\nTotal Time: {total_duration}\n\n"

        self.summary_content.configure(text=summary_text)

# start program
if __name__ == "__main__":
    root = ctk.CTk()
    root.minsize(600, 450)
    tracker = WorkTimeTracker(root)

    root.mainloop()