from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange
import sqlite3
import os
import sys
from datetime import datetime

# Assicurarsi che la directory src sia nel path di importazione
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database_manager import SoldByRomoDatabase

# Configurazione per cercare i template nella directory principale invece che in src/templates
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'romo_secret_key_change_in_production'  # Per sicurezza in produzione usare un valore segreto

# Percorso assoluto al database nella directory principale del progetto
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sold_by_romo.db'))

# Connessione al database
db = SoldByRomoDatabase(db_path)

# Form per aggiungere/aggiornare articoli all'inventario
class InventoryForm(FlaskForm):
    nome_articolo = StringField('Nome Articolo', validators=[DataRequired()])
    colore = StringField('Colore', validators=[DataRequired()])
    taglia = StringField('Taglia', validators=[DataRequired()])
    quantita = IntegerField('Quantità', validators=[NumberRange(min=0)])
    prezzo_acquisto = DecimalField('Prezzo di Acquisto', validators=[NumberRange(min=0)])
    prezzo_vendita = DecimalField('Prezzo di Vendita', validators=[NumberRange(min=0)])
    submit = SubmitField('Salva')

# Form per registrare un acquisto
class AcquistoForm(FlaskForm):
    nome_articolo = StringField('Nome Articolo', validators=[DataRequired()])
    colore = StringField('Colore', validators=[DataRequired()])
    taglia = StringField('Taglia', validators=[DataRequired()])
    quantita = IntegerField('Quantità', validators=[NumberRange(min=1)])
    prezzo = DecimalField('Prezzo Unitario', validators=[NumberRange(min=0)])
    fornitore = StringField('Fornitore')
    submit = SubmitField('Registra Acquisto')

# Form per registrare una vendita
class VenditaForm(FlaskForm):
    articolo = StringField('Articolo', validators=[DataRequired()])
    colore = StringField('Colore', validators=[DataRequired()])
    taglia = StringField('Taglia', validators=[DataRequired()])
    quantita = IntegerField('Quantità', validators=[NumberRange(min=1)])
    prezzo_vendita = DecimalField('Prezzo di Vendita', validators=[NumberRange(min=0)])
    categoria = StringField('Categoria')
    genere = SelectField('Genere', choices=[('', 'Seleziona...'), ('Donna', 'Donna'), ('Uomo', 'Uomo'), ('Bambino', 'Bambino'), ('Bambina', 'Bambina')])
    posto = StringField('Posto')
    cash = SelectField('Pagamento Cash', choices=[('True', 'Si'), ('False', 'No')])
    sconto = DecimalField('Sconto', default=0, validators=[NumberRange(min=0)])
    submit = SubmitField('Registra Vendita')

# Form di ricerca
class SearchForm(FlaskForm):
    search_term = StringField('Cerca')
    submit = SubmitField('Cerca')

@app.route('/')
def index():
    """Homepage con collegamenti alle varie sezioni"""
    return render_template('index.html')

@app.route('/inventario')
def inventario():
    """Visualizza l'inventario completo"""
    search = request.args.get('search', '')
    colore = request.args.get('colore', '')
    solo_disponibili = request.args.get('disponibili', '') == 'true'
    sort_by = request.args.get('sort', 'quantita')
    sort_order = request.args.get('order', 'desc')

    db.connect()

    # Costruisci la query in base ai parametri
    conditions = []
    params = []

    if search:
        conditions.append("nome_articolo LIKE ?")
        params.append(f"%{search}%")
    if colore:
        conditions.append("colore LIKE ?")
        params.append(f"%{colore}%")
    if solo_disponibili:
        conditions.append("quantita > 0")

    # Crea la query SQL
    sql = "SELECT * FROM Inventario"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    # Gestione ordinamento
    valid_sort_fields = {
        'taglia': 'taglia',
        'quantita': 'quantita',
        'nome': 'nome_articolo',
        'colore': 'colore',
        'prezzo_acquisto': 'prezzo_acquisto',
        'prezzo_vendita': 'prezzo_vendita'
    }

    sort_field = valid_sort_fields.get(sort_by, 'quantita')
    sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'

    sql += f" ORDER BY {sort_field} {sort_direction}"
    
    db.cursor.execute(sql, params)
    items = db.cursor.fetchall()
    
    # Calcola il totale del valore della merce filtrata
    totale_acquisto = 0
    totale_vendita = 0
    totale_quantita = 0
    
    for item in items:
        quantita = item['quantita']
        prezzo_acquisto = item['prezzo_acquisto']
        prezzo_vendita = item['prezzo_vendita']
        
        totale_quantita += quantita
        totale_acquisto += quantita * prezzo_acquisto
        totale_vendita += quantita * prezzo_vendita
    
    db.close()
    return render_template('inventario.html', items=items, search=search, colore=colore, 
                           totale_acquisto=totale_acquisto, totale_vendita=totale_vendita, 
                           totale_quantita=totale_quantita, current_sort=sort_by, current_order=sort_order)

@app.route('/inventario/aggiungi', methods=['GET', 'POST'])
def aggiungi_articolo():
    """Aggiunge un articolo all'inventario"""
    form = InventoryForm()
    
    if form.validate_on_submit():
        db.connect()
        
        # Verifica se l'articolo esiste già
        db.cursor.execute(
            "SELECT ID_inventario FROM Inventario WHERE nome_articolo = ? AND colore = ? AND taglia = ?",
            (form.nome_articolo.data, form.colore.data, form.taglia.data)
        )
        existing_item = db.cursor.fetchone()
        
        if existing_item:
            # Aggiorna articolo esistente
            db.cursor.execute(
                """UPDATE Inventario 
                SET quantita = ?, prezzo_acquisto = ?, prezzo_vendita = ? 
                WHERE ID_inventario = ?""",
                (form.quantita.data, form.prezzo_acquisto.data, 
                form.prezzo_vendita.data, existing_item['ID_inventario'])
            )
            db.conn.commit()
            flash(f"Articolo '{form.nome_articolo.data}' aggiornato con successo!", 'success')
        else:
            # Aggiungi nuovo articolo
            db.aggiungi_articolo_inventario(
                form.nome_articolo.data,
                form.taglia.data,
                form.colore.data,
                form.quantita.data,
                float(form.prezzo_acquisto.data),
                float(form.prezzo_vendita.data)
            )
            flash(f"Articolo '{form.nome_articolo.data}' aggiunto con successo!", 'success')
        
        db.close()
        return redirect(url_for('inventario'))
    
    return render_template('form_articolo.html', form=form, title="Aggiungi Articolo")

@app.route('/inventario/modifica/<int:id>', methods=['GET', 'POST'])
def modifica_articolo(id):
    """Modifica un articolo esistente nell'inventario"""
    db.connect()
    
    # Ottieni i dati dell'articolo
    db.cursor.execute("SELECT * FROM Inventario WHERE ID_inventario = ?", (id,))
    item = db.cursor.fetchone()
    
    if not item:
        db.close()
        flash("Articolo non trovato", 'error')
        return redirect(url_for('inventario'))
    
    form = InventoryForm()
    
    if request.method == 'GET':
        # Popola il form con i dati esistenti
        form.nome_articolo.data = item['nome_articolo']
        form.colore.data = item['colore']
        form.taglia.data = item['taglia']
        form.quantita.data = item['quantita']
        form.prezzo_acquisto.data = item['prezzo_acquisto']
        form.prezzo_vendita.data = item['prezzo_vendita']
    
    if form.validate_on_submit():
        # Aggiorna i dati dell'articolo
        db.cursor.execute(
            """UPDATE Inventario 
            SET nome_articolo = ?, colore = ?, taglia = ?, 
            quantita = ?, prezzo_acquisto = ?, prezzo_vendita = ? 
            WHERE ID_inventario = ?""",
            (form.nome_articolo.data, form.colore.data, form.taglia.data, 
            int(form.quantita.data), float(form.prezzo_acquisto.data), 
            float(form.prezzo_vendita.data), id)
        )
        db.conn.commit()
        db.close()
        
        flash(f"Articolo '{form.nome_articolo.data}' aggiornato con successo!", 'success')
        return redirect(url_for('inventario'))
    
    db.close()
    return render_template('form_articolo.html', form=form, title="Modifica Articolo")

@app.route('/acquisti')
def acquisti():
    """Visualizza la lista degli acquisti"""
    db.connect()
    db.cursor.execute("SELECT * FROM Acquisti ORDER BY data DESC")
    items = db.cursor.fetchall()
    db.close()
    return render_template('acquisti.html', items=items)

@app.route('/acquisti/aggiungi', methods=['GET', 'POST'])
def aggiungi_acquisto():
    """Registra un nuovo acquisto"""
    form = AcquistoForm()
    
    if form.validate_on_submit():
        db.connect()
        
        # Verifica se l'articolo esiste nell'inventario
        db.cursor.execute(
            "SELECT ID_inventario FROM Inventario WHERE nome_articolo = ? AND colore = ? AND taglia = ?",
            (form.nome_articolo.data, form.colore.data, form.taglia.data)
        )
        item = db.cursor.fetchone()
        
        if item:
            id_articolo = item['ID_inventario']
        else:
            # Articolo non esistente, chiedi se aggiungerlo
            flash("Articolo non trovato nell'inventario. Verrai reindirizzato a un form per aggiungerlo prima.", 'warning')
            return redirect(url_for('aggiungi_articolo'))
        
        # Registra l'acquisto
        db.registra_acquisto(
            id_articolo=id_articolo,
            nome_articolo=form.nome_articolo.data,
            taglia=form.taglia.data,
            colore=form.colore.data,
            quantita=form.quantita.data,
            prezzo=float(form.prezzo.data),
            data=datetime.now().strftime('%Y-%m-%d'),
            fornitore=form.fornitore.data
        )
        
        db.close()
        flash(f"Acquisto registrato con successo!", 'success')
        return redirect(url_for('acquisti'))
    
    return render_template('form_acquisto.html', form=form)

@app.route('/acquisti/modifica/<int:id>', methods=['GET', 'POST'])
def modifica_acquisto(id):
    """Modifica un acquisto esistente"""
    db.connect()
    
    # Ottieni i dettagli dell'acquisto
    acquisto = db.ottieni_acquisto(id)
    if not acquisto:
        db.close()
        flash("Acquisto non trovato", 'error')
        return redirect(url_for('acquisti'))
    
    form = AcquistoForm()
    
    if request.method == 'GET':
        # Popola il form con i dati dell'acquisto
        form.nome_articolo.data = acquisto['nome_articolo']
        form.colore.data = acquisto['colore']
        form.taglia.data = acquisto['taglia']
        form.quantita.data = acquisto['quantita']
        form.prezzo.data = acquisto['prezzo']
        form.fornitore.data = acquisto['fornitore']
    
    if form.validate_on_submit():
        # Aggiorna l'acquisto
        result = db.aggiorna_acquisto(
            id_acquisto=id,
            nome_articolo=form.nome_articolo.data,
            taglia=form.taglia.data,
            colore=form.colore.data,
            quantita=form.quantita.data,
            prezzo=float(form.prezzo.data),
            data=acquisto['data'],  # Mantieni la data originale
            fornitore=form.fornitore.data
        )
        
        db.close()
        
        if result:
            flash("Acquisto aggiornato con successo!", 'success')
        else:
            flash("Errore nell'aggiornamento dell'acquisto", 'error')
            
        return redirect(url_for('acquisti'))
    
    db.close()
    return render_template('form_acquisto.html', form=form, title="Modifica Acquisto")

@app.route('/acquisti/elimina/<int:id>')
def elimina_acquisto(id):
    """Elimina un acquisto"""
    db.connect()
    result = db.elimina_acquisto(id)
    db.close()
    
    if result:
        flash("Acquisto eliminato con successo!", 'success')
    else:
        flash("Errore nell'eliminazione dell'acquisto", 'error')
    
    return redirect(url_for('acquisti'))

@app.route('/vendite')
def vendite():
    """Visualizza la lista delle vendite"""
    posto = request.args.get('posto', '')
    
    db.connect()
    
    # Costruisci la query in base ai parametri
    query = "SELECT * FROM Vendite"
    params = []
    
    # Aggiungi filtro per posto se specificato
    if posto:
        query += " WHERE posto = ?"
        params.append(posto)
    
    query += " ORDER BY data DESC"
    
    # Esegui la query
    db.cursor.execute(query, params)
    items = db.cursor.fetchall()
    
    db.close()
    return render_template('vendite.html', items=items, posto_filtro=posto)

@app.route('/vendite/aggiungi', methods=['GET', 'POST'])
def aggiungi_vendita():
    """Registra una nuova vendita"""
    form = VenditaForm()
    
    if form.validate_on_submit():
        db.connect()
        
        # Verifica se l'articolo esiste nell'inventario e ha quantità sufficiente
        db.cursor.execute(
            "SELECT ID_inventario, prezzo_acquisto FROM Inventario WHERE nome_articolo = ? AND colore = ? AND taglia = ?",
            (form.articolo.data, form.colore.data, form.taglia.data)
        )
        item = db.cursor.fetchone()
        
        if not item:
            flash("Articolo non trovato nell'inventario.", 'error')
            db.close()
            return redirect(url_for('aggiungi_vendita'))
        
        # Registra la vendita
        cash = form.cash.data == 'True'
        db.registra_vendita(
            articolo=form.articolo.data,
            colore=form.colore.data,
            taglia=form.taglia.data,
            prezzo_vendita=float(form.prezzo_vendita.data),
            prezzo_acquisto=item['prezzo_acquisto'],
            data=datetime.now().strftime('%Y-%m-%d'),
            categoria=form.categoria.data,
            genere=form.genere.data,
            posto=form.posto.data,
            cash=cash,
            sconto=float(form.sconto.data)
        )
        
        db.close()
        flash(f"Vendita registrata con successo!", 'success')
        return redirect(url_for('vendite'))
    
    return render_template('form_vendita.html', form=form)

@app.route('/api/articoli', methods=['GET'])
def api_articoli():
    """API per ottenere articoli filtrati per ricerca"""
    search = request.args.get('q', '')
    
    db.connect()
    items = db.cerca_articolo_inventario(search)
    db.close()
    
    # Converti a dizionari per la serializzazione JSON
    result = []
    for item in items:
        result.append({
            'id': item['ID_inventario'],
            'nome': item['nome_articolo'],
            'colore': item['colore'],
            'taglia': item['taglia'],
            'quantita': item['quantita'],
            'prezzo_acquisto': item['prezzo_acquisto'],
            'prezzo_vendita': item['prezzo_vendita']
        })
    
    return jsonify(result)

@app.route('/api/suggest/articoli', methods=['GET'])
def api_suggest_articoli():
    """API per ottenere suggerimenti di nomi articoli"""
    term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not term or len(term) < 2:
        return jsonify([])
    
    db.connect()
    
    # Cerca articoli che iniziano con il termine di ricerca
    db.cursor.execute("""
    SELECT DISTINCT nome_articolo 
    FROM Inventario 
    WHERE LOWER(nome_articolo) LIKE LOWER(?) 
    ORDER BY nome_articolo
    LIMIT ?
    """, (f"{term}%", limit))
    
    items = db.cursor.fetchall()
    result = [item['nome_articolo'] for item in items]
    
    db.close()
    return jsonify(result)

@app.route('/api/suggest/colori', methods=['GET'])
def api_suggest_colori():
    """API per ottenere suggerimenti di colori"""
    term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if len(term) < 1:
        db.connect()
        # Ritorna i primi colori più comuni
        db.cursor.execute("""
        SELECT colore, COUNT(*) as count 
        FROM Inventario 
        GROUP BY colore 
        ORDER BY count DESC
        LIMIT ?
        """, (limit,))
        
        items = db.cursor.fetchall()
        result = [item['colore'] for item in items]
        db.close()
        return jsonify(result)
    
    db.connect()
    
    # Cerca colori che iniziano con il termine di ricerca
    db.cursor.execute("""
    SELECT DISTINCT colore 
    FROM Inventario 
    WHERE LOWER(colore) LIKE LOWER(?) 
    ORDER BY colore
    LIMIT ?
    """, (f"{term}%", limit))
    
    items = db.cursor.fetchall()
    result = [item['colore'] for item in items]
    
    db.close()
    return jsonify(result)

@app.route('/statistiche')
def statistiche():
    """Mostra statistiche di vendita"""
    data_inizio = request.args.get('data_inizio', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
    data_fine = request.args.get('data_fine', datetime.now().strftime('%Y-%m-%d'))
    
    db.connect()
    
    # Calcola statistiche
    stats = db.calcola_profitti_periodo(data_inizio, data_fine)
    
    # Top articoli venduti
    db.cursor.execute("""
    SELECT Articolo, Colore, COUNT(*) as num_vendite, SUM(Prezzo_vendita) as totale_vendite
    FROM Vendite 
    WHERE data BETWEEN ? AND ?
    GROUP BY Articolo, Colore
    ORDER BY num_vendite DESC
    LIMIT 10
    """, (data_inizio, data_fine))
    top_items = db.cursor.fetchall()
    
    db.close()
    
    return render_template(
        'statistiche.html', 
        stats=stats, 
        top_items=top_items,
        data_inizio=data_inizio,
        data_fine=data_fine
    )

@app.route('/posti')
def posti():
    """Visualizza statistiche di vendita per posto"""
    db.connect()
    
    # Ottieni statistiche per posto
    stats_posti = db.get_statistiche_per_posto()
    
    db.close()
    
    return render_template('posti.html', stats_posti=stats_posti)

if __name__ == '__main__':
    # Assicurati che la directory templates esista
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # In ambiente Docker dobbiamo ascoltare su 0.0.0.0 (tutti gli indirizzi IP)
    # per permettere connessioni dall'host al container
    app.run(host='0.0.0.0', port=5000, debug=True)
