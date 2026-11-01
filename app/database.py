"""Small shared connection adapter for local SQLite or cloud PostgreSQL."""
import os, sqlite3
from contextlib import contextmanager

class PostgresAdapter:
    def __init__(self, connection): self.connection=connection
    def execute(self, query, parameters=()):
        # Application SQL is fixed; only value placeholders are translated.
        return self.connection.execute(query.replace("?", "%s").replace("created REAL", "created DOUBLE PRECISION"),parameters)

@contextmanager
def connect(path, cloud=True):
    url=os.environ.get("DATABASE_URL") if cloud else None
    if url:
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(url,row_factory=dict_row,connect_timeout=15) as db:
            yield PostgresAdapter(db)
    else:
        db=sqlite3.connect(path,timeout=15);db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()
