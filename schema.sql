-- schema.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    saldo INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    mode_otomatis INTEGER DEFAULT 1,
    persentase_menang INTEGER DEFAULT 30,
    min_menang INTEGER DEFAULT 10000,
    max_menang INTEGER DEFAULT 100000,
    default_saldo INTEGER DEFAULT 100000
);
