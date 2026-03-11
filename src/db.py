import json
import csv
import os
import sqlite3
import time
import shutil
from datetime import datetime

from .config import Config as _conf


def ensure_database(database_folder: str, 
                    filename: str = _conf.db_file) -> str:
    os.makedirs(database_folder, exist_ok=True)
    db_path = os.path.join(database_folder, filename)
    conn = sqlite3.connect(db_path)
    conn.execute(_conf.txt_ensure_db)
    conn.commit()
    conn.close()
    return db_path

def change_database(dest_folder: str) -> str:
    os.makedirs(dest_folder, exist_ok=True)
    return os.path.join(dest_folder, _conf.db_file)

def clone_database(src_path: str, dest_path: str):
    shutil.copy2(src_path, dest_path)

def new_database(dest_path: str):
    conn = sqlite3.connect(dest_path)
    conn.execute(_conf.txt_new_db)
    conn.commit()
    conn.close()

def insert_entry(db_path: str, date: str, start: str, end: str, duration: str):
    conn = sqlite3.connect(db_path)
    conn.execute(
        _conf.txt_insert_entry,
        (date, start, end, duration),
    )
    conn.commit()
    conn.close()

def summary_by_date(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(_conf.txt_summary_by_date)
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
    rows = conn.execute(_conf.txt_export_csv).fetchall()
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
                    _conf.txt_import_csv,
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
        _conf.txt_export_json
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
    rows = conn.execute(_conf.txt_all_entries).fetchall()
    conn.close()
    return rows

def month_and_week_stats(db_path: str):
    conn = sqlite3.connect(db_path)
    month_rows = conn.execute(_conf.txt_month_rows).fetchall()
    week_rows = conn.execute(_conf.txt_week_rows).fetchall()
    conn.close()
    return month_rows, week_rows
