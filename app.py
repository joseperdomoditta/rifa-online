from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
import csv
import os
from io import StringIO

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flask'
DB_NAME = 'rifa.db'
CLAVE_ADMIN = "@JoseperNpep963"
PRECIO = 20000 # PRECIO POR NUMERO

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS numeros 
                 (id TEXT PRIMARY KEY, estado TEXT, comprador TEXT, fecha TEXT)''')
    count = c.execute("SELECT COUNT(*) FROM numeros").fetchone()[0]
    if count == 0:
        for i in range(0, 100):
            numero_str = f"{i:02d}"
            c.execute("INSERT INTO numeros (id, estado) VALUES (?,?)", (numero_str, 'disponible'))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db()
    numeros = conn.execute('SELECT * FROM numeros ORDER BY id').fetchall()
    vendidos = conn.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'").fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    return render_template('index.html', numeros=numeros, precio=PRECIO, total=total, vendidos=vendidos)

@app.route('/comprar/<string:numero>', methods=['POST'])
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
        flash(f"Numero {numero} reservado para {comprador} por ${PRECIO:,}", "success")
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
    
    conn = get_db()
    vendidos = conn.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'").fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    return render_template('admin.html', precio=PRECIO, total=total, vendidos=vendidos)

@app.route('/admin/reporte')
def reporte():
    clave = request.args.get('clave')
    if clave!= CLAVE_ADMIN:
        return "No autorizado", 403
    conn = get_db()
    numeros = conn.execute('SELECT * FROM numeros ORDER BY id').fetchall()
    vendidos = conn.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'").fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['REPORTE RIFA VIVEIN'])
    cw.writerow(['Precio por numero', f"${PRECIO:,}"])
    cw.writerow(['Total Recaudado', f"${total:,}"])
    cw.writerow(['Numeros Vendidos', f"{vendidos}/100"])
    cw.writerow([])
    cw.writerow(['Numero', 'Estado', 'Comprador', 'Fecha'])
    
    for n in numeros:
        cw.writerow([n['id'], n['estado'], n['comprador'] or '', n['fecha'] or ''])
    
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=reporte_rifa_VIVEIN.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
