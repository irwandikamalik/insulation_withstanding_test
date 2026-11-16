from app.database.database_base import DatabaseBase

class TestResultDatabase(DatabaseBase):
    def __init__(self):
        super().__init__()
        self.create_table()

    def create_table(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    judgment TEXT NOT NULL,
                    test_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    finish_time TEXT,
                    operator_id TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    model TEXT NOT NULL,
                    history_tag TEXT NOT NULL,
                    door_top TEXT NOT NULL,
                    door_bottom TEXT NOT NULL,
                    voltage REAL,
                    withstanding_voltage REAL,
                    withstanding_normal REAL,
                    withstanding_max REAL,
                    insulation_test REAL,
                    insulation_normal REAL,
                    insulation_min REAL,
                    error_message TEXT
                )
            """)

    def save_result(self, result):
        columns = [
            "judgment", "test_date", "start_time", "finish_time",
            "operator_id", "operator_name", "model", "history_tag",
            "door_top", "door_bottom", "voltage",
            "withstanding_voltage", "withstanding_normal",
            "withstanding_max", "insulation_test",
            "insulation_normal", "insulation_min", "error_message"
        ]
        placeholders = ",".join("?" for _ in columns)
        sql = (
            f"INSERT INTO test_results ({','.join(columns)}) "
            f"VALUES ({placeholders})"
        )
        with self.get_connection() as con:
            con.execute(sql, tuple(result.get(c) for c in columns))

    def get_recent_results(self, limit=100):
        with self.get_connection() as con:
            return con.execute("""
                SELECT result_id, judgment, test_date, start_time,
                       operator_id, model, history_tag
                FROM test_results
                ORDER BY result_id DESC LIMIT ?
            """, (limit,)).fetchall()
