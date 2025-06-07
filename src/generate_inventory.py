import sqlite3
import os
from database_manager import SoldByRomoDatabase

def generate_inventory_from_sales(db_path="sold_by_romo.db"):
    """
    Genera l'inventario basato sui dati delle vendite.
    Crea un record univoco per ogni combinazione di articolo+colore+taglia
    con quantità impostata a 0.
    """
    db = SoldByRomoDatabase(db_path)
    
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return False
    
    db.connect()
    
    try:
        # Ottieni combinazioni uniche di articolo, colore, taglia dalla tabella Vendite
        query = """
        SELECT DISTINCT 
            Articolo as nome_articolo, 
            Colore as colore, 
            Taglia as taglia,
            AVG(Prezzo_acquisto) as prezzo_acquisto, 
            AVG(Prezzo_vendita) as prezzo_vendita
        FROM Vendite
        GROUP BY Articolo, Colore, Taglia
        """
        
        db.cursor.execute(query)
        unique_items = db.cursor.fetchall()
        
        # Verifica se l'inventario è già popolato
        db.cursor.execute("SELECT COUNT(*) FROM Inventario")
        inventory_count = db.cursor.fetchone()[0]
        
        if inventory_count > 0:
            user_input = input("L'inventario contiene già degli articoli. Vuoi continuare e aggiungere nuovi articoli? (s/n): ")
            if user_input.lower() != 's':
                print("Operazione annullata.")
                return False
        
        # Aggiungi ogni articolo unico all'inventario con quantità 0
        count = 0
        for item in unique_items:
            # Verifica se l'articolo esiste già nell'inventario
            check_query = "SELECT COUNT(*) FROM Inventario WHERE nome_articolo = ? AND colore = ? AND taglia = ?"
            db.cursor.execute(check_query, (item['nome_articolo'], item['colore'], item['taglia']))
            exists = db.cursor.fetchone()[0] > 0
            
            if not exists:
                result = db.aggiungi_articolo_inventario(
                    nome_articolo=item['nome_articolo'],
                    taglia=item['taglia'],
                    colore=item['colore'],
                    quantita=0,  # Imposta quantità a 0
                    prezzo_acquisto=item['prezzo_acquisto'],
                    prezzo_vendita=item['prezzo_vendita']
                )
                
                if result:
                    count += 1
        
        db.conn.commit()
        print(f"Inventario generato con successo: {count} nuovi articoli aggiunti.")
        
        return True
    
    except sqlite3.Error as e:
        print(f"Errore nella generazione dell'inventario: {e}")
        return False
    
    finally:
        db.close()

def main():
    print("Generazione dell'inventario basato sui dati delle vendite...")
    success = generate_inventory_from_sales()
    
    if success:
        print("Operazione completata con successo!")
    else:
        print("Si sono verificati problemi durante l'operazione.")

if __name__ == "__main__":
    main()
