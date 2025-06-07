import os
import csv
import sqlite3
from datetime import datetime
from database_manager import SoldByRomoDatabase

def parse_date(date_str):
    """Converte una stringa di data nel formato 'Month day, year' in 'YYYY-MM-DD'"""
    try:
        # Parse la data dal formato "Month day, year"
        date_obj = datetime.strptime(date_str.strip(), "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print(f"Errore nel parsing della data: {date_str}")
        return None

def import_vendite_from_csv(csv_path, db_path="sold_by_romo.db"):
    """Importa i dati delle vendite dal file CSV nel database SQLite"""
    db = SoldByRomoDatabase(db_path)
    
    # Se il database non esiste, crealo usando lo script SQL
    if not os.path.exists(db_path):
        script_path = "create_sold_by_romo_db.sql"
        if os.path.exists(script_path):
            db.create_tables_from_sql_file(script_path)
        else:
            print(f"File SQL {script_path} non trovato.")
            return False
    else:
        db.connect()
    
    count = 0
    errors = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            for row in csv_reader:
                try:
                    # Estrai i dati dalle colonne CSV
                    articolo = row.get("Articolo - Listino", "").split(" (", 1)[0]  # Rimuovi URL tra parentesi
                    data = parse_date(row.get("Date", ""))
                    colore = row.get("Colore", "")
                    taglia = row.get("Taglia", "")
                    categoria = row.get("Categoria", "")
                    genere = row.get("Genere", "")
                    posto = row.get("Posto", "")
                    cash = row.get("CASH", "").lower() != "no"  # Si presume "No" per pagamenti non in contanti
                    
                    # Converti i prezzi in numeri float
                    try:
                        prezzo_vendita = float(row.get("Prezzo vendita", 0))
                    except ValueError:
                        prezzo_vendita = 0
                    
                    try:
                        prezzo_acquisto = float(row.get("Prezzo di acquisto", 0))
                    except ValueError:
                        prezzo_acquisto = 0
                    
                    try:
                        sconto = float(row.get("Sconto", 0))
                    except ValueError:
                        sconto = 0
                    
                    # Inserisci la vendita nel database
                    result = db.registra_vendita(
                        articolo=articolo,
                        colore=colore,
                        taglia=taglia,
                        prezzo_vendita=prezzo_vendita,
                        prezzo_acquisto=prezzo_acquisto,
                        data=data,
                        categoria=categoria,
                        genere=genere,
                        posto=posto,
                        cash=cash,
                        sconto=sconto
                    )
                    
                    if result:
                        count += 1
                    else:
                        errors += 1
                        print(f"Errore nell'inserimento della vendita: {articolo}, {colore}, {taglia}")
                
                except Exception as e:
                    errors += 1
                    print(f"Errore nella riga del CSV: {e}")
    
    except Exception as e:
        print(f"Errore nell'apertura o lettura del file CSV: {e}")
        return False
    
    finally:
        db.close()
    
    print(f"Importazione completata: {count} vendite importate, {errors} errori")
    return count > 0

def main():
    csv_path = r"c:\Users\Utente\Desktop\Mercato_Romo\Vendite 19_09_24-6_06_25\Vendite 6829a159cc57434c82ca41b3517bb834_all.csv"
    
    if not os.path.exists(csv_path):
        print(f"Il file CSV non esiste: {csv_path}")
        return
    
    print(f"Importazione vendite dal file: {csv_path}")
    success = import_vendite_from_csv(csv_path)
    
    if success:
        print("Importazione completata con successo!")
    else:
        print("Si sono verificati problemi durante l'importazione.")

if __name__ == "__main__":
    main()
