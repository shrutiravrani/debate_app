import sqlite3

def init_db():
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    with open("dump.sql") as f:
        cursor.executescript(f.read())
    db.commit()
    db.close()

if __name__ == '__main__':
    init_db()
