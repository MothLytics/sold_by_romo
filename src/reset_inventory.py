import sqlite3
import os
from database_manager import SoldByRomoDatabase

def reset_inventory_quantities(db_path="sold_by_romo.db"):
    """
    Azzera tutte le quantità nel database dell'inventario.
    
    Args:
        db_path: Percorso al database
    
    Returns:
        bool: True se l'operazione è riuscita, False altrimenti
    """
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return False
    
    try:
        db = SoldByRomoDatabase(db_path)
        db.connect()
        
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
        db.close()
        return True
    except sqlite3.Error as e:
        print(f"Errore durante l'azzeramento dell'inventario: {e}")
        return False
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return False

if __name__ == "__main__":
    print("=== AZZERAMENTO QUANTITÀ INVENTARIO ===")
    reset_inventory_quantities()
    print("Operazione completata.")
