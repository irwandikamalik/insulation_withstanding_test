
from app.database.database_base import DatabaseBase


class OperatorDatabase(DatabaseBase):

    def __init__(self):
        super().__init__()
        self.create_table()

    def create_table(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS operators (
                    operator_id TEXT PRIMARY KEY,
                    operator_name TEXT NOT NULL
                )
            """)

    def get_all_operators(self):
        with self.get_connection() as con:
            return con.execute("""
                SELECT operator_id, operator_name
                FROM operators
                ORDER BY operator_id
            """).fetchall()

    def get_operator(self, operator_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT operator_id, operator_name
                FROM operators
                WHERE operator_id = ?
            """, (operator_id,)).fetchone()

    def add_operator(self, operator_id, operator_name):
        with self.get_connection() as con:
            con.execute("""
                INSERT INTO operators (
                    operator_id,
                    operator_name
                )
                VALUES (?, ?)
            """, (operator_id, operator_name))

    def update_operator(self, old_id, new_id, new_name):
        with self.get_connection() as con:
            con.execute("""
                UPDATE operators
                SET
                    operator_id = ?,
                    operator_name = ?
                WHERE operator_id = ?
            """, (new_id, new_name, old_id))

    def delete_operator(self, operator_id):
        with self.get_connection() as con:
            con.execute("""
                DELETE FROM operators
                WHERE operator_id = ?
            """, (operator_id,))
