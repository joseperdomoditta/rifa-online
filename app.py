from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flask'
DB_NAME = 'rifa.db'
CLAVE_ADMIN = "RIFA2026"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS numeros 
                 (id INTEGER PRIMARY KEY, estado TEXT, comprador TEXT, fecha TEXT)''')
    # Rellenar solo si está vacía
    count = c.execute("SELECT COUNT(*) FROM numeros").fetchone()[0]
    if count == 0:
        for i in range(1, 101):
            c.execute("INSERT INTO numeros (id, estado) VALUES (?,?)", (i, 'disponible'))
        print("Base de datos creada con 100 numeros")
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

@app.route('/comprar/<int:numero>', methods=['POST'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
