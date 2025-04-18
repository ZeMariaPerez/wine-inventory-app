CREATE TABLE credentials (
    id INTEGER PRIMARY KEY,
    user TEXT,
    hashed_pw TEXT
);

CREATE TABLE wines (
    id INTEGER PRIMARY KEY,
    wine_name TEXT,
    brand TEXT,
    region TEXT,
    wine_type TEXT,
    subtype TEXT DEFAULT '-',
    "year" INTEGER,
    alcohol NUMERIC,
    bottle_size NUMERIC,
    description TEXT,
);

CREATE UNIQUE INDEX unique_wines_index ON wines (brand, wine_name, region, wine_type, subtype, "year", alcohol, bottle_size);

CREATE TABLE inventory (
    id  INTEGER PRIMARY KEY,
    wine_id INTEGER,
    selling_price NUMERIC,
    buying_price NUMERIC
    quantity INTEGER,
    FOREIGN KEY (wine_id) REFERENCES wines(id)
);

CREATE TABLE inventory_backup (
    id  INTEGER PRIMARY KEY,
    wine_id INTEGER,
    selling_price NUMERIC,
    buying_price NUMERIC,
    quantity INTEGER,
    FOREIGN KEY (wine_id) REFERENCES wines(id)
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    wine_id INTEGER,
    bottle_quantity INTEGER,
    sale_value NUMERIC,
    sale_date DATETIME,
    FOREIGN KEY (wine_id) REFERENCES wines(id)
);
