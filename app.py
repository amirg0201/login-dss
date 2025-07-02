from flask import Flask, render_template, request, redirect, session, url_for
from database import SessionLocal, init_db
from models.user import Usuario

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Base de datos en memoria
init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = SessionLocal()
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if db.query(Usuario).filter_by(username=user).first():
            db.close()
            return 'Usuario ya registrado.'
        nuevo = Usuario(username=user, password=pwd)
        db.add(nuevo)
        db.commit()
        db.close()
        return redirect(url_for('login'))
    db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = SessionLocal()
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        registro = db.query(Usuario).filter_by(username=user, password=pwd).first()
        db.close()
        if registro:
            session['usuario'] = user
            return redirect(url_for('welcome'))
        return 'Credenciales incorrectas'
    db.close()
    return render_template('login.html')

@app.route('/welcome')
def welcome():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
