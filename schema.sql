-- schema.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    saldo INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode_otomatis BOOLEAN DEFAULT 0,
    persentase_menang INTEGER DEFAULT 0,
    min_menang INTEGER DEFAULT 50000,
    max_menang INTEGER DEFAULT 100000,
    default_saldo INTEGER DEFAULT 100000
);
