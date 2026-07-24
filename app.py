from flask import Flask, render_template, request, redirect, url_for, flash, Response
import psycopg2
import psycopg2.extras
import os
import csv
from io import StringIO
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_vivein_2026'
CLAVE_ADMIN = "@JoseperNpep963"
PRECIO = 20000

def get_db():
    url = urlparse(os.environ['DATABASE_URL'])
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS numeros 
                 (id TEXT PRIMARY KEY, estado TEXT, comprador TEXT, fecha TIMESTAMP)''')
    c.execute("SELECT COUNT(*) FROM numeros")
    if c.fetchone()[0] == 0:
        for i in range(0, 100):
            numero_str = f"{i:02d}"
            c.execute("INSERT INTO numeros (id, estado) VALUES (%s,%s)", (numero_str, 'disponible'))
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute('SELECT * FROM numeros ORDER BY id')
    numeros = c.fetchall()
    c.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'")
    vendidos = c.fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    return render_template('index.html', numeros=numeros, precio=PRECIO, total=total, vendidos=vendidos)

@app.route('/comprar/<string:numero>', methods=['POST'])
def comprar(numero):
    comprador = request.form.get('nombre', 'Anónimo')
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("UPDATE numeros SET estado = 'ocupado', comprador = %s, fecha = NOW() WHERE id = %s AND estado = 'disponible'", (comprador, numero))
        if c.rowcount == 1:
            conn.commit()
            flash(f"¡Listo! Número {numero} reservado para {comprador}", "success")
        else:
            conn.rollback()
            flash(f"El número {numero} ya fue tomado", "error")
    except:
        conn.rollback()
        flash("Error, intenta de nuevo", "error")
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        clave = request.form.get('clave')
        if clave == CLAVE_ADMIN:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE numeros SET estado = 'disponible', comprador = NULL, fecha = NULL")
            conn.commit()
            conn.close()
            flash("Rifa reseteada", "success")
            return redirect(url_for('index'))
        else:
            flash("Clave incorrecta", "error")
    
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'")
    vendidos = c.fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    return render_template('admin.html', precio=PRECIO, total=total, vendidos=vendidos)

@app.route('/admin/reporte')
def reporte():
    clave = request.args.get('clave')
    if clave!= CLAVE_ADMIN:
        return "No autorizado", 403
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute('SELECT * FROM numeros ORDER BY id')
    numeros = c.fetchall()
    c.execute("SELECT COUNT(*) FROM numeros WHERE estado='ocupado'")
    vendidos = c.fetchone()[0]
    total = vendidos * PRECIO
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['REPORTE RIFA VIVEIN'])
    cw.writerow(['Precio por numero', f"${PRECIO:,}"])
    cw.writerow(['Total Recaudado', f"${total:,}"])
    cw.writerow(['Numeros Vendidos', f"{vendidos}/100"])
    cw.writerow(['Meta: $2,000,000'])
    cw.writerow([])
    cw.writerow(['Numero', 'Estado', 'Comprador', 'Fecha'])
    for n in numeros:
        cw.writerow([n['id'], n['estado'], n['comprador'] or '', n['fecha'] or ''])
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=reporte_rifa_VIVEIN.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
