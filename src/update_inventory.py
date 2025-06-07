import os
import csv
import sqlite3
from datetime import datetime
from database_manager import SoldByRomoDatabase

def update_inventory_item(db, nome_articolo, colore, taglia, quantita):
    """
    Aggiorna un articolo nell'inventario o lo crea se non esiste.
    
    Args:
        db: Istanza di SoldByRomoDatabase
        nome_articolo: Nome dell'articolo
        colore: Colore dell'articolo
        taglia: Taglia dell'articolo
        quantita: Nuova quantità dell'articolo
    
    Returns:
        tuple: (success, messaggio, id_articolo)
    """
    try:
        # Cerca l'articolo nell'inventario
        query = """
        SELECT ID_inventario, quantita, prezzo_acquisto, prezzo_vendita 
        FROM Inventario 
        WHERE nome_articolo = ? AND colore = ? AND taglia = ?
        """
        db.cursor.execute(query, (nome_articolo, colore, taglia))
        result = db.cursor.fetchone()
        
        if result:
            # Articolo esistente, aggiorna la quantità
            id_inventario = result['ID_inventario']
            db.aggiorna_quantita_inventario(id_inventario, quantita)
            return True, f"Quantità aggiornata per {nome_articolo} ({colore}, {taglia}): {quantita}", id_inventario
        else:
            # Articolo non esistente, chiedi informazioni aggiuntive
            print(f"\nArticolo non trovato nell'inventario: {nome_articolo} ({colore}, {taglia})")
            
            try:
                prezzo_acquisto = float(input("Inserisci prezzo di acquisto: "))
                prezzo_vendita = float(input("Inserisci prezzo di vendita: "))
            except ValueError:
                return False, "Errore: i prezzi devono essere valori numerici", None
            
            # Crea nuovo articolo
            id_inventario = db.aggiungi_articolo_inventario(
                nome_articolo=nome_articolo,
                taglia=taglia,
                colore=colore,
                quantita=quantita,
                prezzo_acquisto=prezzo_acquisto,
                prezzo_vendita=prezzo_vendita
            )
            
            if id_inventario:
                return True, f"Nuovo articolo aggiunto: {nome_articolo} ({colore}, {taglia}) - Quantità: {quantita}", id_inventario
            else:
                return False, "Errore nell'aggiunta del nuovo articolo", None
    
    except sqlite3.Error as e:
        return False, f"Errore database: {e}", None

def manual_inventory_update(db_path="sold_by_romo.db"):
    """Funzione principale per l'aggiornamento manuale dell'inventario"""
    db = SoldByRomoDatabase(db_path)
    
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return False
    
    db.connect()
    print("=== AGGIORNAMENTO MANUALE DELL'INVENTARIO ===")
    print("Per terminare, lascia vuoto il nome dell'articolo")
    
    try:
        while True:
            print("\nInserisci i dettagli dell'articolo (lascia vuoto per terminare):")
            nome_articolo = input("Nome articolo: ")
            if not nome_articolo:
                break
            
            colore = input("Colore: ")
            taglia = input("Taglia: ")
            
            try:
                quantita = int(input("Quantità: "))
            except ValueError:
                print("Errore: la quantità deve essere un numero intero")
                continue
            
            success, message, _ = update_inventory_item(db, nome_articolo, colore, taglia, quantita)
            print(message)
            
        print("\nAggiornamento inventario completato!")
        return True
    
    except Exception as e:
        print(f"Errore: {e}")
        return False
    
    finally:
        db.close()

def import_from_csv(csv_path, db_path="sold_by_romo.db"):
    """Importa aggiornamenti dell'inventario da un file CSV"""
    db = SoldByRomoDatabase(db_path)
    
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return False
    
    if not os.path.exists(csv_path):
        print(f"Il file CSV {csv_path} non esiste.")
        return False
    
    db.connect()
    count = 0
    errors = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            for row in csv_reader:
                try:
                    nome_articolo = row.get("Articolo", "").strip()
                    colore = row.get("Colore", "").strip()
                    taglia = row.get("Taglia", "").strip()
                    
                    try:
                        quantita = int(row.get("Quantità", "0"))
                    except ValueError:
                        print(f"Errore: quantità non valida per {nome_articolo} {colore} {taglia}")
                        errors += 1
                        continue
                    
                    success, message, _ = update_inventory_item(db, nome_articolo, colore, taglia, quantita)
                    
                    if success:
                        count += 1
                        print(message)
                    else:
                        errors += 1
                        print(f"ERRORE: {message}")
                
                except Exception as e:
                    errors += 1
                    print(f"Errore nella riga del CSV: {e}")
        
        print(f"\nImportazione completata: {count} articoli aggiornati, {errors} errori")
        return count > 0
    
    except Exception as e:
        print(f"Errore nell'apertura o lettura del file CSV: {e}")
        return False
    
    finally:
        db.close()

def main():
    print("=== AGGIORNAMENTO INVENTARIO ===")
    print("1. Aggiornamento manuale")
    print("2. Importa da file CSV")
    
    try:
        choice = int(input("\nSeleziona un'opzione (1-2): "))
        
        if choice == 1:
            manual_inventory_update()
        elif choice == 2:
            csv_path = input("Inserisci il percorso del file CSV: ")
            import_from_csv(csv_path)
        else:
            print("Opzione non valida")
    
    except ValueError:
        print("Inserisci un numero valido")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
