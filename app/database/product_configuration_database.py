from app.instruments.instrument_definitions import (
    INSTRUMENT_MODELS,
)
from app.database.database_base import DatabaseBase

class ProductConfigurationDatabase(DatabaseBase):
    """Stores test parameters per product model and instrument type."""

    def __init__(self):
        super().__init__()
        self.create_tables()
        self.seed_product_models()

    def create_tables(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS product_models (
                    product_model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL UNIQUE,
                    history_prefix TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS product_instrument_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_model_id INTEGER NOT NULL,
                    instrument_model TEXT NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL DEFAULT '',
                    UNIQUE(product_model_id, instrument_model, setting_key),
                    FOREIGN KEY(product_model_id)
                        REFERENCES product_models(product_model_id)
                        ON DELETE CASCADE
                )
            """)

    def seed_product_models(self):
        # Europe prefix is intentionally blank: enter the real prefix in
        # Manage Product Test Configuration rather than guessing it.
        with self.get_connection() as con:
            con.execute("""
                INSERT OR IGNORE INTO product_models(model_name, history_prefix)
                VALUES ('Japan', '*13J')
            """)
            con.execute("""
                INSERT OR IGNORE INTO product_models(model_name, history_prefix)
                VALUES ('Europe', '')
            """)

    def get_product_models(self, enabled_only=True):
        sql = """
            SELECT product_model_id, model_name, history_prefix, enabled
            FROM product_models
        """
        if enabled_only:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY model_name"
        with self.get_connection() as con:
            return con.execute(sql).fetchall()

    def get_product_model(self, product_model_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT product_model_id, model_name, history_prefix, enabled
                FROM product_models WHERE product_model_id = ?
            """, (product_model_id,)).fetchone()

    def get_product_model_by_name(self, model_name):
        with self.get_connection() as con:
            return con.execute("""
                SELECT product_model_id, model_name, history_prefix, enabled
                FROM product_models WHERE model_name = ?
            """, (model_name,)).fetchone()

    def add_product_model(self, model_name, history_prefix=''):
        with self.get_connection() as con:
            con.execute("""
                INSERT INTO product_models(model_name, history_prefix)
                VALUES (?, ?)
            """, (model_name.strip(), history_prefix.strip()))

    def update_product_model(self, product_model_id, model_name, history_prefix, enabled):
        with self.get_connection() as con:
            con.execute("""
                UPDATE product_models
                SET model_name = ?, history_prefix = ?, enabled = ?
                WHERE product_model_id = ?
            """, (model_name.strip(), history_prefix.strip(), enabled, product_model_id))

    def save_instrument_settings(self, product_model_id, instrument_model, settings):
        valid_keys = {
            key for key, _ in INSTRUMENT_MODELS[instrument_model]
        }
        with self.get_connection() as con:
            for key, value in settings.items():
                if key not in valid_keys:
                    continue
                con.execute("""
                    INSERT INTO product_instrument_settings(
                        product_model_id, instrument_model, setting_key, setting_value
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(product_model_id, instrument_model, setting_key)
                    DO UPDATE SET setting_value = excluded.setting_value
                """, (product_model_id, instrument_model, key, str(value).strip()))

    def get_instrument_settings(self, product_model_id, instrument_model):
        with self.get_connection() as con:
            rows = con.execute("""
                SELECT setting_key, setting_value
                FROM product_instrument_settings
                WHERE product_model_id = ? AND instrument_model = ?
            """, (product_model_id, instrument_model)).fetchall()
            return dict(rows)

    def get_complete_configuration(self, product_model_id):
        model = self.get_product_model(product_model_id)
        if not model:
            raise ValueError("Product model not found.")
        config = {
            "product_model_id": model[0],
            "model_name": model[1],
            "history_prefix": model[2],
            "instruments": {}
        }
        for instrument_model in INSTRUMENT_MODELS:
            config["instruments"][instrument_model] = (
                self.get_instrument_settings(product_model_id, instrument_model)
            )
        return config
