import sqlite3
import os
from database_manager import SoldByRomoDatabase
import subprocess
import time

def stop_docker_container():
    """Stops the Docker container if it's running"""
    try:
        # Check if container is running
        result = subprocess.run(["docker", "ps", "-q", "-f", "name=mercato-romo-container"], 
                            capture_output=True, text=True)
        
        if result.stdout.strip():
            print("Container Docker trovato in esecuzione. Arresto in corso...")
            subprocess.run(["docker", "stop", "mercato-romo-container"], check=True)
            print("Container Docker fermato con successo.")
            # Wait a few seconds to ensure all resources are released
            time.sleep(3)
        else:
            print("Container Docker non in esecuzione.")
    except Exception as e:
        print(f"Errore con Docker: {e}")

def clean_inventory_duplicates(db_path="sold_by_romo.db"):
    """
    Rimuove i duplicati dall'inventario, combinando le quantità di articoli identici.
    Gli articoli sono considerati duplicati se hanno lo stesso nome_articolo, colore e taglia,
    ignorando differenze di maiuscole e minuscole.
    
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
        
        # 1. Prendi tutti i record dalla tabella Inventario
        print("Caricamento inventario completo...")
        db.cursor.execute("SELECT * FROM Inventario")
        all_items = db.cursor.fetchall()
        
        print(f"Totale articoli nell'inventario: {len(all_items)}")
        
        # Converti ogni record in un dizionario per facilitare l'elaborazione
        inventory_items = []
        for item in all_items:
            inventory_items.append({
                'ID_inventario': item['ID_inventario'],
                'nome_articolo': item['nome_articolo'].strip().lower() if item['nome_articolo'] else '',
                'taglia': item['taglia'].strip().lower() if item['taglia'] else '',
                'colore': item['colore'].strip().lower() if item['colore'] else '',
                'quantita': item['quantita'],
                'prezzo_acquisto': item['prezzo_acquisto'],
                'prezzo_vendita': item['prezzo_vendita'],
                'original_nome': item['nome_articolo'],
                'original_taglia': item['taglia'],
                'original_colore': item['colore']
            })
        
        # 2. Raggruppa gli articoli per nome_articolo, colore e taglia (case insensitive)
        print("Identificazione dei duplicati (ignorando maiuscole e minuscole)...")
        groups = {}
        for item in inventory_items:
            key = (item['nome_articolo'], item['taglia'], item['colore'])
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        # Trova i gruppi con più di un articolo (duplicati)
        duplicates = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"Trovati {len(duplicates)} gruppi di duplicati.")
        
        if not duplicates:
            print("Nessun duplicato trovato. Il database è già pulito.")
            db.close()
            return True
        
        # Per ogni gruppo di duplicati
        items_processed = 0
        for key, items in duplicates.items():
            nome, taglia, colore = key
            
            # Calcola le statistiche combinate
            total_quantity = sum(item['quantita'] for item in items)
            avg_purchase_price = sum(item['prezzo_acquisto'] for item in items) / len(items)
            avg_sale_price = sum(item['prezzo_vendita'] for item in items) / len(items)
            
            # Ordina gli articoli per ID e prendi il più vecchio (ID più basso)
            items.sort(key=lambda x: x['ID_inventario'])
            item_to_keep = items[0]
            items_to_delete = items[1:]
            
            # Print details of what we're consolidating
            original_items = [f"{item['original_nome']} ({item['original_colore']}, {item['original_taglia']})" for item in items]
            print(f"\nConsolidando: {', '.join(original_items)}")
            print(f"  ID mantenuto: {item_to_keep['ID_inventario']}, IDs eliminati: {[i['ID_inventario'] for i in items_to_delete]}")
            print(f"  Quantità totale: {total_quantity}")
            
            # Aggiorna il record da mantenere
            db.cursor.execute("""
            UPDATE Inventario 
            SET quantita = ?, prezzo_acquisto = ?, prezzo_vendita = ?
            WHERE ID_inventario = ?
            """, (total_quantity, avg_purchase_price, avg_sale_price, item_to_keep['ID_inventario']))
            
            # Elimina i duplicati
            for item in items_to_delete:
                db.cursor.execute("DELETE FROM Inventario WHERE ID_inventario = ?", (item['ID_inventario'],))
                items_processed += 1
        
        # Commit delle modifiche
        db.conn.commit()
        
        # Verifica finale
        db.cursor.execute("SELECT COUNT(*) as count FROM Inventario")
        final_count = db.cursor.fetchone()['count']
        initial_count = len(all_items)
        
        print("\n=== RISULTATO PULIZIA ===")
        print(f"Articoli iniziali: {initial_count}")
        print(f"Articoli eliminati: {items_processed}")
        print(f"Articoli finali: {final_count}")
        print(f"Gruppi duplicati processati: {len(duplicates)}")
        
        # Controllo di coerenza
        if final_count != (initial_count - items_processed):
            print("\nATTENZIONE: Il conteggio finale non corrisponde al previsto!")
            print("Questo potrebbe indicare un problema durante l'elaborazione.")
        else:
            print("\nPulizia completata con successo!")
        
        db.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Errore database: {e}")
        return False
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== PULIZIA DUPLICATI INVENTARIO (VERSIONE MIGLIORATA) ===")
    
    # Stop the Docker container automatically
    stop_docker_container()
    
    # Clean duplicates
    print("\nPulizia dei duplicati in corso...")
    success = clean_inventory_duplicates()
    
    if success:
        print("\nOperazione completata! Il database è stato pulito dai duplicati.")
        print("Per riavviare il container Docker, esegui:")
        print("docker start mercato-romo-container")
    else:
        print("\nOperazione fallita. Controlla gli errori e riprova.")
