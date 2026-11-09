
import sqlite3, json, os
from datetime import datetime

class VehicleRegistry:
    def __init__(self,path="data/vehicles.db"):
        os.makedirs(os.path.dirname(path) or ".",exist_ok=True)
        self.db=sqlite3.connect(path)
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles(
          id INTEGER PRIMARY KEY AUTOINCREMENT, plate TEXT UNIQUE NOT NULL,
          vehicle_type TEXT DEFAULT '', brand TEXT DEFAULT '', owner TEXT DEFAULT '',
          color TEXT DEFAULT '', blacklisted INTEGER DEFAULT 0, notes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS detections(
          id INTEGER PRIMARY KEY AUTOINCREMENT, plate TEXT, ocr_conf REAL,
          detector_conf REAL, source TEXT, frame INTEGER, timestamp TEXT,
          blacklisted INTEGER, matched_target TEXT);
        """)
        self.db.commit()
    def add_vehicle(self,plate,vehicle_type="",brand="",owner="",color="",blacklisted=False,notes=""):
        self.db.execute("""INSERT INTO vehicles(plate,vehicle_type,brand,owner,color,blacklisted,notes)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(plate) DO UPDATE SET
        vehicle_type=excluded.vehicle_type,brand=excluded.brand,owner=excluded.owner,
        color=excluded.color,blacklisted=excluded.blacklisted,notes=excluded.notes""",
        (plate.upper(),vehicle_type,brand,owner,color,int(blacklisted),notes))
        self.db.commit()
    def blacklist(self):
        rows=self.db.execute("SELECT plate FROM vehicles WHERE blacklisted=1").fetchall()
        return [r["plate"] for r in rows]
    def match_blacklist(self,plate):
        from anpr import blacklist_match
        return blacklist_match(plate,self.blacklist())
    def log_detection(self,plate,ocr_conf,det_conf,source,frame,match):
        self.db.execute("""INSERT INTO detections
        (plate,ocr_conf,detector_conf,source,frame,timestamp,blacklisted,matched_target)
        VALUES(?,?,?,?,?,?,?,?)""",
        (plate,ocr_conf,det_conf,str(source),frame,datetime.now().isoformat(timespec="seconds"),
         int(bool(match)),match))
        self.db.commit()
        if match: print(f"BLACKLIST ALERT: {plate} matched {match}")
    def close(self): self.db.close()
