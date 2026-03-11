from dataclasses import dataclass

@dataclass
class Config:
# Main-Window
    lbl_status: str = "Bereit zum Starten"
    lbl_title = "Work Time Tracker"
    lbl_time = "00:00:00"
    
    font = "Segoe UI"


