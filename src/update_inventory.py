import os
import csv
import sqlite3
from datetime import datetime
from database_manager import SoldByRomoDatabase

# Percorso del file del listino prezzi
PREZZI_CSV = "listino prezzi 115f56f3c32b807886cadeac7940d8e3.csv"

# Dizionario globale per memorizzare i prezzi
prezzi_articoli = {}

def carica_prezzi():
    """
    Carica i prezzi dal file CSV del listino prezzi nel dizionario globale prezzi_articoli.
    Il formato previsto è: Articolo,Costo,Prezzo di vendita,Categoria,Genere
    """
    global prezzi_articoli
    prezzi_articoli = {}
    
    if not os.path.exists(PREZZI_CSV):
        print(f"Attenzione: File del listino prezzi non trovato: {PREZZI_CSV}")
        return False
        
    try:
        # Apre il file in modalità binaria per gestire l'encoding correttamente
        with open(PREZZI_CSV, 'rb') as file:
            raw_data = file.read()
            
            # Rileva l'encoding
            if raw_data.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
                encoding = 'utf-8-sig'  # utf-8 with BOM
            else:
                # Prova diverse codifiche
                for enc in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        raw_data.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    encoding = 'cp1252'  # Fallback
            
            # Legge il file con la codifica rilevata
            content = raw_data.decode(encoding, errors='replace')
            reader = csv.DictReader(content.splitlines())
            
            for row in reader:
                nome_articolo = row.get("Articolo", "").strip()
                if nome_articolo:
                    # Ottiene i valori dei prezzi e pulisce
                    costo_str = row.get("Costo", "0").strip()
                    vendita_str = row.get("Prezzo di vendita", "0").strip()
                    
                    # Rimuovi simboli euro e gestisci virgole/punti
                    costo_str = costo_str.replace('€', '').replace('€', '').strip()
                    vendita_str = vendita_str.replace('€', '').replace('€', '').strip()
                    
                    try:
                        # Gestisce formati diversi (9.00, 9,00)
                        costo = costo_str.replace(',', '.')
                        vendita = vendita_str.replace(',', '.')
                        
                        prezzo_acquisto = float(costo)
                        prezzo_vendita = float(vendita)
                        
                        # Salva nel dizionario
                        prezzi_articoli[nome_articolo] = {
                            "prezzo_acquisto": prezzo_acquisto,
                            "prezzo_vendita": prezzo_vendita,
                            "categoria": row.get("Categoria", "").strip(),
                            "genere": row.get("Genere", "").strip()
                        }
                    except ValueError:
                        print(f"Errore nella conversione dei prezzi per: {nome_articolo}")
                        print(f"Valori originali: Costo='{costo_str}', Vendita='{vendita_str}'")
            
        print(f"Listino prezzi caricato: {len(prezzi_articoli)} articoli trovati")
        return len(prezzi_articoli) > 0
        
    except Exception as e:
        print(f"Errore nella lettura del file dei prezzi: {e}")
        return False

def update_inventory_item(db, nome_articolo, colore, taglia, quantita):
    """
    Aggiorna un articolo nell'inventario o lo crea se non esiste.
    Utilizza il listino prezzi caricato per determinare i prezzi automaticamente.
    
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
            # Articolo non esistente, cerca nel listino prezzi
            print(f"\nArticolo non trovato nell'inventario: {nome_articolo} ({colore}, {taglia})")
            
            # Verifica che i prezzi siano caricati
            if not prezzi_articoli:
                carica_prezzi()
                
            # Cerca nel listino prezzi
            articolo_info = prezzi_articoli.get(nome_articolo)
            
            if articolo_info:
                prezzo_acquisto = articolo_info["prezzo_acquisto"]
                prezzo_vendita = articolo_info["prezzo_vendita"]
                print(f"Prezzi trovati nel listino: Acquisto €{prezzo_acquisto:.2f}, Vendita €{prezzo_vendita:.2f}")
            else:
                print(f"Articolo non trovato nel listino prezzi: {nome_articolo}")
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
                return True, f"Nuovo articolo aggiunto: {nome_articolo} ({colore}, {taglia}) - Quantità: {quantita} - Prezzi: Acquisto €{prezzo_acquisto:.2f}, Vendita €{prezzo_vendita:.2f}", id_inventario
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

def reset_inventory_quantities(db):
    """Azzera tutte le quantità nel database dell'inventario."""
    try:
        # Query per azzerare tutte le quantità
        query = "UPDATE Inventario SET quantita = 0"
        db.cursor.execute(query)
        db.conn.commit()
        
        # Conta quanti record sono stati aggiornati
        count_query = "SELECT COUNT(*) as count FROM Inventario"
        db.cursor.execute(count_query)
        result = db.cursor.fetchone()
        count = result['count'] if result else 0
        
        print(f"Quantità azzerata per {count} articoli nell'inventario.")
        return True
    except sqlite3.Error as e:
        print(f"Errore durante l'azzeramento dell'inventario: {e}")
        return False

def import_from_csv(csv_path, db_path="sold_by_romo.db", reset_first=False):
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
        # Azzera l'inventario se richiesto
        if reset_first:
            print("\nAzzeramento quantità inventario prima dell'importazione...")
            if not reset_inventory_quantities(db):
                print("Errore durante l'azzeramento dell'inventario. Continuare comunque? (s/n)")
                if input().lower() != 's':
                    print("Importazione annullata.")
                    return False
            else:
                print("Azzeramento completato con successo. Inizio importazione...\n")
                
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
    print("3. Azzera quantità e importa da file CSV")
    
    # Carica il listino prezzi all'avvio
    carica_prezzi()
    
    try:
        choice = int(input("\nSeleziona un'opzione (1-3): "))
        
        if choice == 1:
            manual_inventory_update()
        elif choice == 2:
            csv_path = input("Inserisci il percorso del file CSV: ")
            import_from_csv(csv_path)
        elif choice == 3:
            csv_path = input("Inserisci il percorso del file CSV: ")
            import_from_csv(csv_path, reset_first=True)
        else:
            print("Opzione non valida")
    
    except ValueError:
        print("Inserisci un numero valido")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
