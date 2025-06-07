-- Script per creare il database sold_by_romo con SQLite

-- Creazione della tabella Inventario
CREATE TABLE IF NOT EXISTS Inventario (
    ID_inventario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_articolo TEXT NOT NULL,
    taglia TEXT NOT NULL,
    colore TEXT NOT NULL,
    quantita INTEGER NOT NULL DEFAULT 0,
    prezzo_acquisto REAL NOT NULL,
    prezzo_vendita REAL NOT NULL
);

-- Creazione della tabella Acquisti
CREATE TABLE IF NOT EXISTS Acquisti (
    ID_acquisto INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_articolo INTEGER NOT NULL,
    nome_articolo TEXT NOT NULL,
    taglia TEXT NOT NULL,
    colore TEXT NOT NULL,
    quantita INTEGER NOT NULL,
    prezzo REAL NOT NULL,
    importo REAL NOT NULL,
    data DATE NOT NULL,
    fornitore TEXT NOT NULL,
    FOREIGN KEY (ID_articolo) REFERENCES Inventario(ID_inventario)
);

-- Creazione della tabella Vendite
CREATE TABLE IF NOT EXISTS Vendite (
    ID_vendita INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    Articolo TEXT NOT NULL,
    Colore TEXT NOT NULL,
    Taglia TEXT NOT NULL,
    Categoria TEXT,
    Genere TEXT,
    Posto TEXT,
    CASH BOOLEAN DEFAULT 1,
    Sconto REAL DEFAULT 0,
    Prezzo_vendita REAL NOT NULL,
    Prezzo_acquisto REAL NOT NULL
);

-- Indici per migliorare le performance
CREATE INDEX idx_inventario_nome ON Inventario(nome_articolo);
CREATE INDEX idx_acquisti_data ON Acquisti(data);
CREATE INDEX idx_vendite_data ON Vendite(data);
