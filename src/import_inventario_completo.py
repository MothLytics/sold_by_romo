#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import sqlite3
from database_manager import SoldByRomoDatabase

def import_inventario_from_csv(csv_path, db_path="sold_by_romo.db"):
    """
    Importa i dati dell'inventario da un file CSV nel database.
    
    Args:
        csv_path: Percorso del file CSV
        db_path: Percorso del database SQLite
    
    Returns:
        tuple: (articoli_importati, articoli_aggiornati, errori)
    """
    # Connessione al database
    db = SoldByRomoDatabase(db_path)
    
    # Contatori per statistiche
    articoli_importati = 0
    articoli_aggiornati = 0
    errori = 0
    
    # Verifica che il file esista
    if not os.path.exists(csv_path):
        print(f"Errore: Il file {csv_path} non esiste")
        return (0, 0, 1)
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            # Verifica delle intestazioni
            expected_headers = ["Articolo", "Colore", "Taglia", "Quantità"]
            headers = csv_reader.fieldnames
            
            if not headers or not all(header in headers for header in expected_headers):
                print(f"Errore: Il file CSV non ha le intestazioni corrette. Trovate: {headers}, Attese: {expected_headers}")
                return (0, 0, 1)
            
            # Importazione dei dati
            for row in csv_reader:
                try:
                    nome_articolo = row["Articolo"].strip()
                    colore = row["Colore"].strip()
                    taglia = row["Taglia"].strip()
                    
                    # Converti la quantità in intero
                    try:
                        quantita = int(row["Quantità"])
                    except (ValueError, KeyError):
                        print(f"Errore: Quantità non valida per l'articolo {nome_articolo}, {colore}, {taglia}")
                        errori += 1
                        continue
                    
                    # Cerca se l'articolo esiste già nel database
                    db.cursor.execute("""
                        SELECT ID_inventario, quantita, prezzo_acquisto, prezzo_vendita 
                        FROM Inventario 
                        WHERE nome_articolo = ? AND colore = ? AND taglia = ?
                    """, (nome_articolo, colore, taglia))
                    
                    result = db.cursor.fetchone()
                    
                    if result:
                        # Aggiorna la quantità dell'articolo esistente
                        id_inventario = result["ID_inventario"]
                        db.aggiorna_quantita_inventario(id_inventario, quantita)
                        print(f"Articolo aggiornato: {nome_articolo}, {colore}, {taglia}, quantità: {quantita}")
                        articoli_aggiornati += 1
                    else:
                        # Chiedi il prezzo per il nuovo articolo (in modalità interattiva)
                        print(f"\nNuovo articolo: {nome_articolo}, {colore}, {taglia}, quantità: {quantita}")
                        
                        try:
                            prezzo_acquisto = float(input(f"Prezzo di acquisto per {nome_articolo} ({colore}, {taglia}): "))
                            prezzo_vendita = float(input(f"Prezzo di vendita per {nome_articolo} ({colore}, {taglia}): "))
                        except ValueError:
                            print(f"Errore: i prezzi devono essere valori numerici")
                            errori += 1
                            continue
                        
                        # Aggiungi il nuovo articolo
                        id_inventario = db.aggiungi_articolo_inventario(
                            nome_articolo=nome_articolo,
                            taglia=taglia,
                            colore=colore,
                            quantita=quantita,
                            prezzo_acquisto=prezzo_acquisto,
                            prezzo_vendita=prezzo_vendita
                        )
                        
                        if id_inventario:
                            print(f"Nuovo articolo aggiunto con ID: {id_inventario}")
                            articoli_importati += 1
                        else:
                            print(f"Errore nell'aggiunta dell'articolo: {nome_articolo}, {colore}, {taglia}")
                            errori += 1
                
                except Exception as e:
                    print(f"Errore durante l'elaborazione della riga: {row}. Errore: {str(e)}")
                    errori += 1
                    continue
    
    except Exception as e:
        print(f"Errore durante l'apertura/lettura del file CSV: {str(e)}")
        return (articoli_importati, articoli_aggiornati, errori + 1)
    
    finally:
        # Salvataggio delle modifiche
        db.conn.commit()
        
        # Stampa le statistiche
        print("\n--- Importazione completata ---")
        print(f"Articoli aggiunti: {articoli_importati}")
        print(f"Articoli aggiornati: {articoli_aggiornati}")
        print(f"Errori riscontrati: {errori}")
        
    return (articoli_importati, articoli_aggiornati, errori)

def main():
    """Funzione principale"""
    # Posizione del file CSV e del database
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, '..'))
    
    csv_path = os.path.join(root_dir, 'inventario_completo.csv')
    db_path = os.path.join(root_dir, 'sold_by_romo.db')
    
    print(f"Importazione inventario da: {csv_path}")
    print(f"Database: {db_path}")
    
    # Esegui l'importazione
    import_inventario_from_csv(csv_path, db_path)

if __name__ == "__main__":
    main()
