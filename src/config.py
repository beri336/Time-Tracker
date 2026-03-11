from dataclasses import dataclass

@dataclass
class Config:
# Main-Window
    lbl_status: str = "Bereit zum Starten"
    lbl_title = "Work Time Tracker"
    lbl_time = "00:00:00"
    
    font = "Segoe UI"
    db_file = "work_time.db"

# Database
    txt_ensure_db = """
        CREATE TABLE IF NOT EXISTS work_time (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            duration   TEXT NOT NULL
        )
    """
    txt_new_db = """
        CREATE TABLE IF NOT EXISTS work_time (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            duration   TEXT NOT NULL
        )
    """
    txt_insert_entry = "INSERT INTO work_time (date, start_time, end_time, duration) VALUES (?, ?, ?, ?)"
    txt_summary_by_date = """
        SELECT date,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY date
        ORDER BY date DESC
    """
    txt_export_csv = "SELECT date, start_time, end_time, duration FROM work_time"
    txt_import_csv = "INSERT INTO work_time (date, start_time, end_time, duration) VALUES (?, ?, ?, ?)"
    txt_export_json = "SELECT id, date, start_time, end_time, duration FROM work_time ORDER BY date DESC"
    txt_all_entries = "SELECT id, date, start_time, end_time, duration FROM work_time ORDER BY date DESC, start_time DESC"
    txt_month_rows = """
        SELECT substr(date, 4, 7) AS month,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY month
        ORDER BY month DESC
    """
    txt_week_rows = """
        SELECT strftime('%Y-KW%W',
                   substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)) AS week,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY week
        ORDER BY week DESC
    """
