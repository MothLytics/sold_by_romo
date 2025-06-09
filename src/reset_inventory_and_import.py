import os
import csv
import sqlite3
import shutil
import subprocess
import time
from datetime import datetime
import sys

# Assicuriamoci che il container Docker sia fermo
def stop_docker_container():
    print("Verifica dello stato del container Docker...")
    try:
        # Controlla se il container esiste e sta girando
        result = subprocess.run(["docker", "ps", "-q", "-f", "name=mercato-romo-container"], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("Container Docker trovato in esecuzione. Arresto in corso...")
            subprocess.run(["docker", "stop", "mercato-romo-container"], check=True)
            print("Container Docker fermato con successo.")
            # Aspetta qualche secondo per assicurarsi che tutte le risorse siano rilasciate
            time.sleep(3)
            return True
        else:
            print("Container Docker non in esecuzione.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'operazione Docker: {e}")
        return False
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return False

def reset_inventory_and_import(db_path="sold_by_romo.db", csv_path="inventario_completo.csv"):
    """
    Azzera tutte le quantità nel database e importa nuovi dati dal CSV
    """
    # Crea una copia del database originale
    backup_file = f"{db_path}.backup"
    temp_db = f"{db_path}.temp"
    
    print(f"Creazione backup del database: {backup_file}")
    try:
        shutil.copy2(db_path, backup_file)
        print("Backup creato con successo.")
    except Exception as e:
        print(f"Errore nella creazione del backup: {e}")
        return False
    
    try:
        # Crea una copia temporanea per le operazioni
        shutil.copy2(db_path, temp_db)
        
        # Apri la copia temporanea per azzerare le quantità
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Azzera tutte le quantità
        cursor.execute("UPDATE Inventario SET quantita = 0")
        conn.commit()
        
        # Controlla quanti record sono stati modificati
        cursor.execute("SELECT COUNT(*) as count FROM Inventario")
        result = cursor.fetchone()
        count = result['count'] if result else 0
        print(f"Quantità azzerate per {count} articoli nell'inventario.")
        
        # Importa i dati dal CSV
        if not os.path.exists(csv_path):
            print(f"File CSV {csv_path} non trovato.")
            return False
        
        print(f"Importazione dati da {csv_path}...")
        
        # Carica il CSV e aggiorna il database
        updated_count = 0
        error_count = 0
        
        # Carica il listino prezzi se disponibile
        prezzi = {}
        listino_path = "listino prezzi 115f56f3c32b807886cadeac7940d8e3.csv"
        if os.path.exists(listino_path):
            try:
                with open(listino_path, 'rb') as file:
                    raw_data = file.read()
                    
                    # Rileva l'encoding
                    if raw_data.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
                        encoding = 'utf-8-sig'
                    else:
                        encoding = 'utf-8'  # Default
                    
                    # Legge il file con la codifica rilevata
                    content = raw_data.decode(encoding, errors='replace')
                    reader = csv.DictReader(content.splitlines())
                    
                    for row in reader:
                        articolo = row.get("Articolo", "").strip()
                        if articolo:
                            try:
                                costo = float(row.get("Costo", "0").replace('€', '').replace(',', '.').strip())
                                vendita = float(row.get("Prezzo di vendita", "0").replace('€', '').replace(',', '.').strip())
                                prezzi[articolo] = {
                                    "prezzo_acquisto": costo,
                                    "prezzo_vendita": vendita
                                }
                            except ValueError:
                                pass  # Ignora errori di conversione
                
                print(f"Listino prezzi caricato: {len(prezzi)} articoli trovati")
            except Exception as e:
                print(f"Errore nel caricamento del listino prezzi: {e}")
                # Continua anche senza listino prezzi
        
        # Importa i dati dal CSV dell'inventario
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
                        error_count += 1
                        continue
                    
                    # Cerca articolo nel database
                    cursor.execute("""
                    SELECT ID_inventario, quantita, prezzo_acquisto, prezzo_vendita 
                    FROM Inventario 
                    WHERE nome_articolo = ? AND colore = ? AND taglia = ?
                    """, (nome_articolo, colore, taglia))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        # Articolo esistente, aggiorna la quantità
                        id_inventario = result['ID_inventario']
                        cursor.execute("UPDATE Inventario SET quantita = ? WHERE ID_inventario = ?", 
                                     (quantita, id_inventario))
                        updated_count += 1
                    else:
                        # Articolo non esistente, cerca prezzi nel listino prezzi
                        prezzo_info = prezzi.get(nome_articolo)
                        
                        if prezzo_info:
                            prezzo_acquisto = prezzo_info["prezzo_acquisto"]
                            prezzo_vendita = prezzo_info["prezzo_vendita"]
                        else:
                            # Default per articoli non trovati nel listino
                            prezzo_acquisto = 0
                            prezzo_vendita = 0
                            print(f"Articolo non trovato nel listino prezzi: {nome_articolo}")
                        
                        # Inserisci nuovo articolo
                        cursor.execute("""
                        INSERT INTO Inventario (nome_articolo, taglia, colore, quantita, prezzo_acquisto, prezzo_vendita)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (nome_articolo, taglia, colore, quantita, prezzo_acquisto, prezzo_vendita))
                        updated_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Errore nell'importazione: {e}")
        
        # Commit delle modifiche
        conn.commit()
        conn.close()
        
        # Sostituisci il database originale con quello aggiornato
        try:
            os.remove(db_path)
            shutil.copy2(temp_db, db_path)
            print(f"Database aggiornato con successo.")
        except Exception as e:
            print(f"Errore nella sostituzione del database: {e}")
            print(f"Puoi trovare il database aggiornato in: {temp_db}")
            return False
        
        print(f"Importazione completata: {updated_count} articoli aggiornati, {error_count} errori")
        return True
        
    except sqlite3.Error as e:
        print(f"Errore database: {e}")
        return False
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return False
    finally:
        # Pulizia dei file temporanei
        try:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        except:
            pass

if __name__ == "__main__":
    print("=== RESET INVENTARIO E IMPORTAZIONE CSV ===")
    
    # Default path
    db_path = "sold_by_romo.db"
    csv_path = "inventario_completo.csv"
    
    # Usa argomenti da riga di comando se forniti
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    
    # Assicurati che il container Docker sia fermo
    if stop_docker_container():
        # Esegui il reset e l'importazione
        if reset_inventory_and_import(db_path, csv_path):
            print("\nOperazione completata con successo!")
            print("Ora puoi riavviare il container Docker con: docker start mercato-romo-container")
        else:
            print("\nOperazione completata con errori!")
    else:
        print("\nImpossibile procedere a causa di errori con il container Docker.")
        
    input("\nPremi INVIO per terminare...")
