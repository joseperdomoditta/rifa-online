from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
import csv
from io import StringIO
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flask'
DB_NAME = 'rifa.db'
CLAVE_ADMIN = "@JoseperNpep963"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

# BORRAR ESTO DESPUÉS DE 1 DEPLOY
import os
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    init_db()

    
    conn = get_db()
    c = conn.cursor()
    # id ahora es TEXT para poder guardar "00", "01", etc
    c.execute('''CREATE TABLE IF NOT EXISTS numeros 
                 (id TEXT PRIMARY KEY, estado TEXT, comprador TEXT, fecha TEXT)''')
    # Rellenar solo si está vacía
    count = c.execute("SELECT COUNT(*) FROM numeros").fetchone()[0]
    if count == 0:
        for i in range(0, 100): # de 0 a 99
            numero_str = f"{i:02d}" # Formato 00, 01, 02... 99
            c.execute("INSERT INTO numeros (id, estado) VALUES (?,?)", (numero_str, 'disponible'))
        print("Base de datos creada con numeros del 00 al 99")
    conn.commit()
    conn.close()

# Esto fuerza que se cree al iniciar en Render
init_db()

@app.route('/')
def index():
    conn = get_db()
    numeros = conn.execute('SELECT * FROM numeros ORDER BY id').fetchall()
    conn.close()
    return render_template('index.html', numeros=numeros)

@app.route('/comprar/<string:numero>', methods=['POST']) # ahora es string
def comprar(numero):
    comprador = request.form.get('nombre', 'Anónimo')
    conn = get_db()
    c = conn.cursor()
    c.execute("BEGIN TRANSACTION")
    estado_actual = c.execute("SELECT estado FROM numeros WHERE id =?", (numero,)).fetchone()
    if estado_actual and estado_actual['estado'] == 'disponible':
        c.execute("UPDATE numeros SET estado = 'ocupado', comprador =?, fecha = datetime('now') WHERE id =?", 
                  (comprador, numero))
        conn.commit()
        flash(f"Numero {numero} reservado para {comprador}", "success")
    else:
        conn.rollback()
        flash(f"El numero {numero} ya fue tomado", "error")
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        clave = request.form.get('clave')
        if clave == CLAVE_ADMIN:
            conn = get_db()
            conn.execute("UPDATE numeros SET estado = 'disponible', comprador = NULL, fecha = NULL")
            conn.commit()
            conn.close()
            flash("Rifa reseteada", "success")
            return redirect(url_for('index'))
        else:
            flash("Clave incorrecta", "error")
    return render_template('admin.html')

@app.route('/admin/reporte')
def reporte():
    clave = request.args.get('clave')
    if clave!= CLAVE_ADMIN:
        return "No autorizado", 403
    
    conn = get_db()
    numeros = conn.execute('SELECT * FROM numeros ORDER BY id').fetchall()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Numero', 'Estado', 'Comprador', 'Fecha']) # Encabezados
    
    for n in numeros:
        cw.writerow([n['id'], n['estado'], n['comprador'] or '', n['fecha'] or ''])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=reporte_rifa.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
