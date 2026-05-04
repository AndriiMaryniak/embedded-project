-- Схема бази даних Energy Saver IoT

-- Таблиця 1: Збереження телеметрії з датчиків
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')),
    raw_power REAL NOT NULL,
    filtered_power REAL NOT NULL,
    temperature REAL NOT NULL
);

-- ОПТИМІЗАЦІЯ: Індекс для швидкого витягування історії за часом (B-Tree)
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);

-- Таблиця 2: Налаштування системи (динамічні ліміти)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value REAL NOT NULL
);

-- Таблиця 3: Логування тривог та системних подій
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')),
    message TEXT NOT NULL
);

-- ОПТИМІЗАЦІЯ: Індекс для фільтрації тривог
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);

-- Дамп базових налаштувань
INSERT OR IGNORE INTO settings (key, value) VALUES ('power_threshold', 5.0);