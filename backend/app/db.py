import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def init():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY,title TEXT,created_at TEXT,updated_at TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,chat_id TEXT,role TEXT,content TEXT,created_at TEXT)")

def all_rows(sql, args=()):
    with db() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]

def run(sql, args=()):
    with db() as c:
        c.execute(sql, args)
