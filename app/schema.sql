DROP TABLE IF EXISTS kv_store;
DROP TABLE IF EXISTS expense;
DROP TABLE IF EXISTS category;

CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL
);

CREATE TABLE expense (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    category_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    note VARCHAR(128),
    FOREIGN KEY(category_id) REFERENCES category(id)
);

CREATE TABLE kv_store (
    id INTEGER PRIMARY KEY,
    key VARCHAR(64) NOT NULL UNIQUE,
    value VARCHAR(64),
    changed DATETIME NOT NULL
);
