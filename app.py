# app.py

import customtkinter as ctk
import time
import json
from datetime import datetime

class ArbeitszeitTracker:
    def __init__(self, root):
        # GUI
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("Arbeitszeit-Tracker")
        self.root.geometry("400x250")

        self.start_time = None
        self.elapsed_time = 0
        self.running = False

        # central frame
        self.center_frame = ctk.CTkFrame(self.root)
        self.center_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # time label
        self.time_label = ctk.CTkLabel(self.center_frame, text="00:00:00", font=("Helvetica", 28, "bold"))
        self.time_label.pack(pady=(0, 20))

        # buttons frame
        self.buttons_frame = ctk.CTkFrame(self.center_frame)
        self.buttons_frame.pack()

        # buttons with styling
        button_style = {"font": ("Helvetica", 12)}

        self.start_button = ctk.CTkButton(self.buttons_frame, text="Start", command=self.start_timer, **button_style)
        self.start_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.pause_button = ctk.CTkButton(self.buttons_frame, text="Pause", command=self.pause_timer, state="disabled", **button_style)
        self.pause_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.continue_button = ctk.CTkButton(self.buttons_frame, text="Weiter", command=self.continue_timer, state="disabled", **button_style)
        self.continue_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(self.buttons_frame, text="Stop", command=self.stop_timer, state="disabled", **button_style)
        self.stop_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # responsive grid settings
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1)

        # start the clock update
        self.update_clock()

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
            file_date = datetime.now().strftime("%d_%m_%Y")
            work_duration = time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time))

            session_data = {
                "Startzeit": self.session_start,
                "Endzeit": self.session_end,
                "Dauer": work_duration
            }

            # generate file name based on today's date
            file_name = f"arbeitszeit-{file_date}.json"

            try:
                with open(file_name, "r") as f:
                    arbeitszeit_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                arbeitszeit_data = []

            # check if today's data already exists
            date_entry = next((entry for entry in arbeitszeit_data if entry["Datum"] == current_date), None)

            if date_entry:
                # add new session data to the existing date
                date_entry["Sitzungen"].append(session_data)

                # update total time for the day
                total_seconds = sum(
                    int(s["Dauer"].split(":")[0]) * 3600 + int(s["Dauer"].split(":")[1]) * 60 + int(s["Dauer"].split(":")[2])
                    for s in date_entry["Sitzungen"]
                )
                date_entry["Gesamtzeit"] = time.strftime("%H:%M:%S", time.gmtime(total_seconds))
            else:
                # create a new entry for the current date
                date_entry = {
                    "Datum": current_date,
                    "Sitzungen": [session_data],
                    "Gesamtzeit": work_duration
                }
                arbeitszeit_data.append(date_entry)

            # save updated data back to the file
            with open(file_name, "w") as f:
                json.dump(arbeitszeit_data, f, indent=4, ensure_ascii=False)

# start program
if __name__ == "__main__":
    root = ctk.CTk()
    root.minsize(400, 250)
    tracker = ArbeitszeitTracker(root)

    root.mainloop()