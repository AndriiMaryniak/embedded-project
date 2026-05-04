import sqlite3

DB_NAME = "energy_data.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')),
                raw_power REAL NOT NULL,
                filtered_power REAL NOT NULL,
                temperature REAL NOT NULL
            );
            -- Індекс для швидкодії
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')),
                message TEXT NOT NULL
            );
            -- Індекс для тривог
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);

            INSERT OR IGNORE INTO settings (key, value) VALUES ('power_threshold', 5.0);
        ''')
        conn.commit()

def get_threshold():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='power_threshold'")
        res = cursor.fetchone()
        return res[0] if res else 5.0

def save_data(table, **kwargs):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join('?' * len(kwargs))
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(kwargs.values()))
        conn.commit()