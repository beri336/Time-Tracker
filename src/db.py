import json
import csv
import os
import sqlite3
import time
import shutil
from datetime import datetime


def ensure_database(database_folder: str, 
                    filename: str = "work_time.db") -> str:
    os.makedirs(database_folder, exist_ok=True)
    db_path = "work_time.db"
    #db_path = os.path.join(database_folder, filename)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS work_time (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            duration   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    return db_path

def change_database(dest_folder: str) -> str:
    os.makedirs(dest_folder, exist_ok=True)
    return os.path.join(dest_folder, "work_time.db")

def clone_database(src_path: str, dest_path: str):
    shutil.copy2(src_path, dest_path)

def new_database(dest_path: str):
    conn = sqlite3.connect(dest_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS work_time (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            duration   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_entry(db_path: str, date: str, start: str, end: str, duration: str):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO work_time (date, start_time, end_time, duration) VALUES (?, ?, ?, ?)",
        (date, start, end, duration),
    )
    conn.commit()
    conn.close()

def summary_by_date(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY date
        ORDER BY date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "date": r[0],
            "count": r[1],
            "total_seconds": r[2] or 0,
            "total_str": time.strftime("%H:%M:%S", time.gmtime(r[2] or 0)),
        }
        for r in rows
    ]

def export_csv(db_path: str, path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT date, start_time, end_time, duration FROM work_time").fetchall()
    conn.close()
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Datum", 
                    "Anfangszeit", 
                    "Endzeit", 
                    "Dauer"])
        w.writerows(rows)
    return len(rows)

def import_csv(db_path: str, path: str):
    imported = 0
    errors = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        conn = sqlite3.connect(db_path)
        for row in reader:
            try:
                conn.execute(
                    "INSERT INTO work_time (date, start_time, end_time, duration) VALUES (?, ?, ?, ?)",
                    (
                        row.get("Datum") or row.get("Date", ""),
                        row.get("Anfangszeit") or row.get("Start Time", ""),
                        row.get("Endzeit") or row.get("End Time", ""),
                        row.get("Dauer") or row.get("Duration", ""),
                    ),
                )
                imported += 1
            except Exception:
                errors += 1
        conn.commit()
        conn.close()
    return imported, errors

def export_json(db_path: str, path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, date, start_time, end_time, duration FROM work_time ORDER BY date DESC"
    ).fetchall()
    conn.close()
    data = {
        "exported_at":   datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "total_entries": len(rows),
        "entries": [
            {"id": r[0], "date": r[1], "start_time": r[2], "end_time": r[3], "duration": r[4]}
            for r in rows
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return len(rows)

def all_entries(db_path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, date, start_time, end_time, duration FROM work_time ORDER BY date DESC, start_time DESC").fetchall()
    conn.close()
    return rows

def month_and_week_stats(db_path: str):
    conn = sqlite3.connect(db_path)
    month_rows = conn.execute("""
        SELECT substr(date, 4, 7) AS month,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()
    week_rows = conn.execute("""
        SELECT strftime('%Y-KW%W',
                   substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)) AS week,
               COUNT(*),
               SUM(strftime('%s', duration) - strftime('%s', '00:00:00'))
        FROM work_time
        GROUP BY week
        ORDER BY week DESC
    """).fetchall()
    conn.close()
    return month_rows, week_rows
