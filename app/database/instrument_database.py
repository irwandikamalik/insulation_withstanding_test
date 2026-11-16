from app.database.database_base import DatabaseBase


class InstrumentDatabase(DatabaseBase):
    INSTRUMENT_MODELS = {
        "WT310E": [
            ("measurement_function", "Measurement Function"),
            ("voltage_range", "Voltage Range"),
            ("current_range", "Current Range"),
            ("frequency_range", "Frequency Range"),
            ("measurement_interval", "Measurement Interval"),
            ("wiring_mode", "Wiring Mode"),
        ],
        "PCR2000": [
            ("output_voltage", "Output Voltage"),
            ("output_frequency", "Output Frequency"),
            ("current_limit", "Current Limit"),
            ("output_mode", "Output Mode"),
            ("output_state", "Output State"),
        ],
        "TOS9200": [
            ("test_mode", "Test Mode"),
            ("test_voltage", "Test Voltage"),
            ("upper_limit", "Upper Limit"),
            ("lower_limit", "Lower Limit"),
            ("test_time", "Test Time"),
            ("ramp_time", "Ramp Time"),
            ("discharge_time", "Discharge Time"),
        ],
    }

    INTERFACES = ["USB", "GPIB", "TCPIP", "Serial"]

    def __init__(self):
        super().__init__()
        self.create_tables()
        self.seed_instruments()

    def create_tables(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS instruments (
                    instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL UNIQUE,
                    interface TEXT,
                    resource_name TEXT,
                    timeout_ms INTEGER NOT NULL DEFAULT 5000,
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS instrument_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    UNIQUE(instrument_id, setting_key),
                    FOREIGN KEY(instrument_id)
                        REFERENCES instruments(instrument_id)
                        ON DELETE CASCADE
                )
            """)

    def seed_instruments(self):
        with self.get_connection() as con:
            for model in self.INSTRUMENT_MODELS:
                con.execute("""
                    INSERT OR IGNORE INTO instruments(model)
                    VALUES (?)
                """, (model,))

    def get_all_instruments(self):
        with self.get_connection() as con:
            return con.execute("""
                SELECT instrument_id, model, interface,
                       resource_name, timeout_ms, enabled
                FROM instruments ORDER BY model
            """).fetchall()

    def get_instrument(self, instrument_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT instrument_id, model, interface,
                       resource_name, timeout_ms, enabled
                FROM instruments WHERE instrument_id = ?
            """, (instrument_id,)).fetchone()

    def get_instrument_settings(self, instrument_id):
        with self.get_connection() as con:
            rows = con.execute("""
                SELECT setting_key, setting_value
                FROM instrument_settings
                WHERE instrument_id = ?
            """, (instrument_id,)).fetchall()
            return dict(rows)

    def save_instrument(
        self, instrument_id, model, interface,
        resource_name, timeout_ms, enabled, settings
    ):
        if model not in self.INSTRUMENT_MODELS:
            raise ValueError("Unsupported instrument model.")

        with self.get_connection() as con:
            if instrument_id is None:
                cursor = con.execute("""
                    INSERT INTO instruments(
                        model, interface, resource_name,
                        timeout_ms, enabled
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    model, interface, resource_name,
                    timeout_ms, enabled
                ))
                instrument_id = cursor.lastrowid
            else:
                con.execute("""
                    UPDATE instruments
                    SET model = ?, interface = ?, resource_name = ?,
                        timeout_ms = ?, enabled = ?
                    WHERE instrument_id = ?
                """, (
                    model, interface, resource_name,
                    timeout_ms, enabled, instrument_id
                ))

            valid_keys = {
                key for key, _ in self.INSTRUMENT_MODELS[model]
            }
            for key, value in settings.items():
                if key in valid_keys:
                    con.execute("""
                        INSERT INTO instrument_settings(
                            instrument_id, setting_key, setting_value
                        ) VALUES (?, ?, ?)
                        ON CONFLICT(instrument_id, setting_key)
                        DO UPDATE SET setting_value = excluded.setting_value
                    """, (instrument_id, key, value))

            if valid_keys:
                placeholders = ",".join("?" for _ in valid_keys)
                con.execute(f"""
                    DELETE FROM instrument_settings
                    WHERE instrument_id = ?
                    AND setting_key NOT IN ({placeholders})
                """, (instrument_id, *valid_keys))

    def delete_instrument(self, instrument_id):
        with self.get_connection() as con:
            con.execute(
                "DELETE FROM instruments WHERE instrument_id = ?",
                (instrument_id,)
            )