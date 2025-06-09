import sqlite3
import os
from database_manager import SoldByRomoDatabase

def clean_inventory_duplicates(db_path="sold_by_romo.db"):
    """
    Rimuove i duplicati dall'inventario, combinando le quantità di articoli identici.
    Gli articoli sono considerati duplicati se hanno lo stesso nome_articolo, colore e taglia.
    
    Args:
        db_path: Percorso al database
    
    Returns:
        bool: True se l'operazione è riuscita, False altrimenti
    """
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return False
    
    try:
        # Crea una copia di backup del database
        backup_path = f"{db_path}.backup_clean"
        print(f"Creazione backup del database: {backup_path}")
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        # Apri la connessione al database
        db = SoldByRomoDatabase(db_path)
        db.connect()
        
        # 1. Identifica tutti gli articoli unici (nome_articolo, colore, taglia)
        print("Identificazione degli articoli unici...")
        db.cursor.execute("""
        SELECT nome_articolo, colore, taglia, 
               COUNT(*) as num_duplicati,
               SUM(quantita) as quantita_totale,
               AVG(prezzo_acquisto) as prezzo_acquisto_medio,
               AVG(prezzo_vendita) as prezzo_vendita_medio
        FROM Inventario
        GROUP BY nome_articolo, colore, taglia
        HAVING COUNT(*) > 1
        """)
        
        duplicati = db.cursor.fetchall()
        print(f"Trovati {len(duplicati)} gruppi di duplicati.")
        
        if not duplicati:
            print("Nessun duplicato trovato. Il database è già pulito.")
            db.close()
            return True
        
        # Per ogni gruppo di duplicati
        for duplicato in duplicati:
            nome_articolo = duplicato['nome_articolo']
            colore = duplicato['colore']
            taglia = duplicato['taglia']
            quantita_totale = duplicato['quantita_totale']
            prezzo_acquisto = duplicato['prezzo_acquisto_medio']
            prezzo_vendita = duplicato['prezzo_vendita_medio']
            
            # Ottieni tutti gli ID dei duplicati
            db.cursor.execute("""
            SELECT ID_inventario FROM Inventario
            WHERE nome_articolo = ? AND colore = ? AND taglia = ?
            """, (nome_articolo, colore, taglia))
            
            id_list = [row['ID_inventario'] for row in db.cursor.fetchall()]
            
            if len(id_list) <= 1:
                continue  # Salta se non ci sono duplicati
                
            # Mantieni il primo ID e aggiorna le sue informazioni
            id_keep = id_list[0]
            id_to_delete = id_list[1:]
            
            print(f"Consolidando '{nome_articolo}' ({colore}, {taglia}): {len(id_list)} duplicati -> 1 record")
            print(f"  ID mantenuto: {id_keep}, ID da eliminare: {id_to_delete}")
            
            # Aggiorna il record da mantenere con la quantità e prezzi combinati
            db.cursor.execute("""
            UPDATE Inventario 
            SET quantita = ?, prezzo_acquisto = ?, prezzo_vendita = ?
            WHERE ID_inventario = ?
            """, (quantita_totale, prezzo_acquisto, prezzo_vendita, id_keep))
            
            # Elimina i duplicati
            for id_to_del in id_to_delete:
                db.cursor.execute("DELETE FROM Inventario WHERE ID_inventario = ?", (id_to_del,))
        
        # Commit delle modifiche
        db.conn.commit()
        
        # Verifica che non ci siano più duplicati
        db.cursor.execute("""
        SELECT COUNT(*) as count FROM (
            SELECT nome_articolo, colore, taglia, COUNT(*) as num
            FROM Inventario
            GROUP BY nome_articolo, colore, taglia
            HAVING COUNT(*) > 1
        )
        """)
        remaining = db.cursor.fetchone()['count']
        
        if remaining == 0:
            print("\nPulizia completata con successo! Non ci sono più duplicati nell'inventario.")
        else:
            print(f"\nAttenzione: Ci sono ancora {remaining} gruppi di duplicati nell'inventario.")
        
        # Ottieni statistiche finali
        db.cursor.execute("SELECT COUNT(*) as count FROM Inventario")
        total_items = db.cursor.fetchone()['count']
        print(f"Totale articoli nell'inventario dopo la pulizia: {total_items}")
        
        db.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Errore database: {e}")
        return False
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return False

if __name__ == "__main__":
    print("=== PULIZIA DUPLICATI INVENTARIO ===")
    
    # Assicurati che il container Docker sia fermo prima di procedere
    print("ATTENZIONE: Assicurati che il container Docker sia fermo prima di procedere!")
    print("Puoi fermarlo con 'docker stop mercato-romo-container'")
    
    proceed = input("Vuoi procedere con la pulizia dei duplicati? (s/n): ")
    if proceed.lower() == 's':
        success = clean_inventory_duplicates()
        if success:
            print("\nOperazione completata! Ora puoi riavviare il container Docker.")
            print("docker start mercato-romo-container")
        else:
            print("\nOperazione fallita. Controlla gli errori e riprova.")
    else:
        print("Operazione annullata.")
