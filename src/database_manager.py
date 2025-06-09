import sqlite3
import os
from datetime import datetime

class SoldByRomoDatabase:
    def __init__(self, db_path="sold_by_romo.db"):
        """Inizializza la connessione al database."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Stabilisce una connessione al database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Errore nella connessione al database: {e}")
            return False
    
    def close(self):
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()
    
    def create_tables_from_sql_file(self, sql_file_path):
        """Crea le tabelle usando uno script SQL."""
        try:
            if not self.conn:
                self.connect()
            
            with open(sql_file_path, 'r') as file:
                sql_script = file.read()
            
            self.conn.executescript(sql_script)
            self.conn.commit()
            print(f"Database creato con successo da {sql_file_path}")
            return True
        except (sqlite3.Error, IOError) as e:
            print(f"Errore nella creazione delle tabelle: {e}")
            return False
    
    # Funzioni per la tabella Inventario
    def aggiungi_articolo_inventario(self, nome_articolo, taglia, colore, quantita, prezzo_acquisto, prezzo_vendita):
        """Aggiunge un nuovo articolo all'inventario."""
        try:
            if not self.conn:
                self.connect()
            
            sql = """
            INSERT INTO Inventario (nome_articolo, taglia, colore, quantita, prezzo_acquisto, prezzo_vendita)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (nome_articolo, taglia, colore, quantita, prezzo_acquisto, prezzo_vendita))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Errore nell'aggiunta dell'articolo all'inventario: {e}")
            return None
    
    def aggiorna_quantita_inventario(self, id_inventario, nuova_quantita):
        """Aggiorna la quantità di un articolo nell'inventario."""
        try:
            if not self.conn:
                self.connect()
            
            sql = "UPDATE Inventario SET quantita = ? WHERE ID_inventario = ?"
            self.cursor.execute(sql, (nuova_quantita, id_inventario))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Errore nell'aggiornamento della quantità: {e}")
            return False
    
    def cerca_articolo_inventario(self, nome=None, taglia=None, colore=None):
        """Cerca articoli nell'inventario per nome, taglia o colore."""
        try:
            if not self.conn:
                self.connect()
            
            conditions = []
            params = []
            
            if nome:
                conditions.append("nome_articolo LIKE ?")
                params.append(f"%{nome}%")
            if taglia:
                conditions.append("taglia LIKE ?")
                params.append(f"%{taglia}%")
            if colore:
                conditions.append("colore LIKE ?")
                params.append(f"%{colore}%")
            
            sql = "SELECT * FROM Inventario"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Errore nella ricerca dell'articolo: {e}")
            return []
    
    # Funzioni per la tabella Acquisti
    def registra_acquisto(self, id_articolo, nome_articolo, taglia, colore, quantita, prezzo, data=None, fornitore=""):
        """Registra un nuovo acquisto e aggiorna l'inventario."""
        try:
            if not self.conn:
                self.connect()
            
            if data is None:
                data = datetime.now().strftime('%Y-%m-%d')
            
            importo = prezzo * quantita
            
            # Registra l'acquisto
            sql = """
            INSERT INTO Acquisti (ID_articolo, nome_articolo, taglia, colore, quantita, prezzo, importo, data, fornitore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (id_articolo, nome_articolo, taglia, colore, quantita, prezzo, importo, data, fornitore))
            
            # Aggiorna l'inventario
            self.cursor.execute("SELECT quantita FROM Inventario WHERE ID_inventario = ?", (id_articolo,))
            result = self.cursor.fetchone()
            if result:
                quantita_attuale = result[0]
                self.aggiorna_quantita_inventario(id_articolo, quantita_attuale + quantita)
            
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Errore nella registrazione dell'acquisto: {e}")
            return None
    
    def ottieni_acquisti_per_periodo(self, data_inizio, data_fine):
        """Ottiene tutti gli acquisti in un determinato periodo."""
        try:
            if not self.conn:
                self.connect()
            
            sql = "SELECT * FROM Acquisti WHERE data BETWEEN ? AND ?"
            self.cursor.execute(sql, (data_inizio, data_fine))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Errore nell'ottenimento degli acquisti: {e}")
            return []
    
    # Funzioni per la tabella Vendite
    def registra_vendita(self, articolo, colore, taglia, prezzo_vendita, prezzo_acquisto, 
                        data=None, categoria="", genere="", posto="", cash=True, sconto=0):
        """Registra una nuova vendita."""
        try:
            if not self.conn:
                self.connect()
            
            if data is None:
                data = datetime.now().strftime('%Y-%m-%d')
            
            sql = """
            INSERT INTO Vendite (data, Articolo, Colore, Taglia, Categoria, Genere, Posto, CASH, Sconto, Prezzo_vendita, Prezzo_acquisto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (data, articolo, colore, taglia, categoria, genere, posto, cash, sconto, prezzo_vendita, prezzo_acquisto))
            
            # Cerca l'articolo nell'inventario per aggiornare la quantità
            search_sql = "SELECT ID_inventario, quantita FROM Inventario WHERE nome_articolo = ? AND colore = ? AND taglia = ?"
            self.cursor.execute(search_sql, (articolo, colore, taglia))
            result = self.cursor.fetchone()
            
            if result:
                id_inventario, quantita_attuale = result
                if quantita_attuale > 0:
                    # Aggiorna l'inventario decrementando la quantità
                    self.aggiorna_quantita_inventario(id_inventario, quantita_attuale - 1)
            
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Errore nella registrazione della vendita: {e}")
            return None
    
    def ottieni_vendite_per_periodo(self, data_inizio, data_fine):
        """Ottiene tutte le vendite in un determinato periodo."""
        try:
            if not self.conn:
                self.connect()
            
            sql = "SELECT * FROM Vendite WHERE data BETWEEN ? AND ?"
            self.cursor.execute(sql, (data_inizio, data_fine))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Errore nell'ottenimento delle vendite: {e}")
            return []
    
    def calcola_profitti_periodo(self, data_inizio, data_fine):
        """Calcola i profitti in un periodo di tempo specifico."""
        try:
            if not self.conn:
                self.connect()
            
            # Calcola i totali delle vendite
            self.cursor.execute("""
            SELECT COUNT(*) as num_vendite, 
                   SUM(Prezzo_vendita) as totale_vendite,
                   SUM(Prezzo_acquisto) as totale_costo,
                   SUM(Prezzo_vendita - Prezzo_acquisto) as profitto
            FROM Vendite 
            WHERE data BETWEEN ? AND ?
            """, (data_inizio, data_fine))
            
            result = self.cursor.fetchone()
            
            # Converti il risultato in un dizionario con le chiavi attese dal template
            if result:
                return {
                    'numero_vendite': result[0],
                    'ricavo_totale': result[1] or 0,  # Se è None, usa 0
                    'costo_totale': result[2] or 0,   # Se è None, usa 0
                    'profitto_totale': result[3] or 0  # Se è None, usa 0
                }
            else:
                # Restituisci valori predefiniti se non ci sono risultati
                return {
                    'numero_vendite': 0,
                    'ricavo_totale': 0,
                    'costo_totale': 0,
                    'profitto_totale': 0
                }
        except sqlite3.Error as e:
            print(f"Errore nel calcolo dei profitti: {e}")
            # Restituisci valori predefiniti in caso di errore
            return {
                'numero_vendite': 0,
                'ricavo_totale': 0,
                'costo_totale': 0,
                'profitto_totale': 0
            }
    
    def ottieni_acquisto(self, id_acquisto):
        """Ottiene i dettagli di un acquisto specifico."""
        try:
            if not self.conn:
                self.connect()
            
            self.cursor.execute("SELECT * FROM Acquisti WHERE ID_acquisto = ?", (id_acquisto,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Errore nell'ottenimento dell'acquisto: {e}")
            return None
    
    def elimina_acquisto(self, id_acquisto):
        """Elimina un acquisto dal database."""
        try:
            if not self.conn:
                self.connect()
            
            # Elimina l'acquisto
            self.cursor.execute("DELETE FROM Acquisti WHERE ID_acquisto = ?", (id_acquisto,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Errore nell'eliminazione dell'acquisto: {e}")
            return False
    
    def aggiorna_acquisto(self, id_acquisto, nome_articolo, taglia, colore, quantita, prezzo, data, fornitore):
        """Aggiorna un acquisto esistente."""
        try:
            if not self.conn:
                self.connect()
            
            # Calcola l'importo
            importo = float(prezzo) * int(quantita)
            
            # Aggiorna l'acquisto
            self.cursor.execute(
                """UPDATE Acquisti 
                SET nome_articolo = ?, taglia = ?, colore = ?, quantita = ?, 
                prezzo = ?, importo = ?, data = ?, fornitore = ? 
                WHERE ID_acquisto = ?""",
                (nome_articolo, taglia, colore, quantita, prezzo, importo, data, fornitore, id_acquisto)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Errore nell'aggiornamento dell'acquisto: {e}")
            return False

    def get_statistiche_per_posto(self):
        """Recupera le statistiche di vendita raggruppate per posto, ordinate per fatturato decrescente."""
        try:
            if not self.conn:
                self.connect()
            
            # Prima aggiungiamo la stampa di debug per vedere i posti disponibili
            self.cursor.execute("SELECT DISTINCT posto FROM Vendite WHERE posto IS NOT NULL AND posto != ''")
            posti_disponibili = [row[0] for row in self.cursor.fetchall()]
            print(f"POSTI DISPONIBILI: {posti_disponibili}")
            
            # Ottiene la lista dei posti unici con relativo fatturato per poterli ordinare
            self.cursor.execute("""
            SELECT posto, SUM(Prezzo_vendita) as fatturato_totale 
            FROM Vendite 
            WHERE posto IS NOT NULL AND posto != '' 
            GROUP BY posto
            ORDER BY fatturato_totale DESC
            """)
            posti = [row[0] for row in self.cursor.fetchall()]
            
            # Prepariamo il risultato
            risultati = []
            for posto in posti:
                print(f"Elaborazione posto: {posto}")
                # Per ogni posto, calcola le statistiche
                self.cursor.execute("""
                SELECT posto,
                       COUNT(*) as num_vendite,
                       SUM(Prezzo_vendita) as fatturato_totale,
                       MIN(data) as prima_vendita,
                       MAX(data) as ultima_vendita,
                       COUNT(DISTINCT data) as giorni_vendita
                FROM Vendite 
                WHERE posto = ? 
                GROUP BY posto
                """, (posto,))
                stats_posto = self.cursor.fetchone()
                
                # Articoli più venduti in questo posto
                self.cursor.execute("""
                SELECT Articolo, COUNT(*) as quantita, SUM(Prezzo_vendita) as fatturato
                FROM Vendite 
                WHERE posto = ? 
                GROUP BY Articolo
                ORDER BY quantita DESC
                LIMIT 5
                """, (posto,))
                top_articoli = self.cursor.fetchall()
                
                # Aggiunge i dati al risultato
                if stats_posto:
                    self.conn.row_factory = sqlite3.Row  # Assicuriamoci che la row factory sia impostata
                    # Creiamo manualmente il dizionario con i dati corretti
                    stats = {
                        'posto': posto,
                        'num_vendite': stats_posto[1],
                        'fatturato_totale': stats_posto[2],
                        'prima_vendita': stats_posto[3],
                        'ultima_vendita': stats_posto[4],
                        'giorni_vendita': stats_posto[5]
                    }
                    
                    # Convertiamo i top articoli in dizionari
                    articoli_dict = []
                    for art in top_articoli:
                        articoli_dict.append({
                            'Articolo': art[0],
                            'quantita': art[1], 
                            'fatturato': art[2]
                        })
                    
                    stats['top_articoli'] = articoli_dict
                    risultati.append(stats)
            
            return risultati
        except sqlite3.Error as e:
            print(f"Errore nel recupero delle statistiche per posto: {e}")
            return []


# Esempio di utilizzo
if __name__ == "__main__":
    db = SoldByRomoDatabase()
    
    # Controlla se il database esiste
    if not os.path.exists(db.db_path):
        script_path = "create_sold_by_romo_db.sql"
        if os.path.exists(script_path):
            db.create_tables_from_sql_file(script_path)
        else:
            print(f"File SQL {script_path} non trovato.")
    else:
        db.connect()
        print(f"Connesso al database esistente: {db.db_path}")
    
    # Esempi di operazioni
    print("\nOperazioni disponibili:")
    print("1. Aggiungi articolo all'inventario")
    print("2. Registra un acquisto")
    print("3. Registra una vendita")
    print("4. Cerca articoli nell'inventario")
    print("5. Visualizza acquisti per periodo")
    print("6. Visualizza vendite per periodo")
    print("7. Calcola profitti per periodo")
    print("0. Esci")
    
    db.close()
