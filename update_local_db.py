import sqlite3

# Percorso al database locale
db_path = 'sold_by_romo.db'

def update_svasato_mix_prices():
    """Aggiorna i prezzi di tutti gli articoli '35 Svasato Mix' nel database locale"""
    try:
        # Connessione al database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"Connesso al database locale: {db_path}")
        
        # Trova tutti gli articoli '35 Svasato Mix'
        cursor.execute("SELECT ID_inventario, nome_articolo, colore, taglia, prezzo_acquisto, prezzo_vendita FROM Inventario WHERE nome_articolo = '35 Svasato Mix'")
        items = cursor.fetchall()
        
        print(f"Trovati {len(items)} articoli '35 Svasato Mix'")
        for item in cursor.fetchall():
            print(f"ID: {item['ID_inventario']}, Colore: {item['colore']}, Taglia: {item['taglia']}, Prezzo Acquisto: {item['prezzo_acquisto']}, Prezzo Vendita: {item['prezzo_vendita']}")
        
        # Aggiorna i prezzi di tutti gli articoli '35 Svasato Mix'
        cursor.execute("""
        UPDATE Inventario 
        SET prezzo_acquisto = 15.00, prezzo_vendita = 35.00 
        WHERE nome_articolo = '35 Svasato Mix'
        """)
        
        # Commit della transazione
        conn.commit()
        print(f"Aggiornati {cursor.rowcount} articoli '35 Svasato Mix'")
        
        # Verifica gli aggiornamenti
        cursor.execute("SELECT ID_inventario, nome_articolo, colore, taglia, prezzo_acquisto, prezzo_vendita FROM Inventario WHERE nome_articolo = '35 Svasato Mix'")
        updated_items = cursor.fetchall()
        
        print("\nVerifica aggiornamenti:")
        for item in cursor.fetchall():
            print(f"ID: {item['ID_inventario']}, Colore: {item['colore']}, Taglia: {item['taglia']}, Prezzo Acquisto: {item['prezzo_acquisto']}, Prezzo Vendita: {item['prezzo_vendita']}")
        
        # Chiusura della connessione
        conn.close()
        
        print("Aggiornamento database locale completato!")
        return True
    except sqlite3.Error as e:
        print(f"Errore nell'aggiornamento dei prezzi: {e}")
        return False

if __name__ == "__main__":
    update_svasato_mix_prices()
