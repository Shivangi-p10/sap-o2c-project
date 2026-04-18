import sqlite3

conn = sqlite3.connect('o2c.db')
c = conn.cursor()

c.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS materials (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 100
    );

    CREATE TABLE IF NOT EXISTS orders (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        material_id INTEGER,
        quantity    INTEGER,
        total       REAL,
        status      TEXT DEFAULT 'Created',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS payments (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER UNIQUE,
        amount   REAL,
        paid_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        method   TEXT
    );
""")

conn.commit()
conn.close()
print("✅ Database ready!")
