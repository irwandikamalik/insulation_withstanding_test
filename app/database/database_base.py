
import sqlite3
from pathlib import Path


class DatabaseBase:

    def __init__(self):
        # database_base.py berada di:
        # project_root/app/database/database_base.py

        self.project_dir = Path(__file__).resolve().parents[2]

        self.db_dir = self.project_dir / "data"
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.db_dir / "insulation_tester.db"

    def get_connection(self):
        connection = sqlite3.connect(self.db_path)

        connection.execute("PRAGMA foreign_keys = ON")

        return connection
