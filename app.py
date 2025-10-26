from flask import Flask, render_template, request, redirect, session, url_for
from database import SessionLocal, init_db
from models.user import Usuario

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Base de datos en memoria

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = SessionLocal()
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        rol = request.form['rol']  
        if db.query(Usuario).filter_by(username=user).first():
            db.close()
            return 'Usuario ya registrado.'
        nuevo = Usuario(username=user, password=pwd, rol=rol)
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
            session['rol'] = registro.rol
            return redirect(url_for('welcome'))
        return 'Credenciales incorrectas'
    db.close()
    return render_template('login.html')

@app.route('/welcome')
def welcome():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    db = SessionLocal()
    user = db.query(Usuario).filter_by(username=session['usuario']).first()

    usuarios = None
    if session['rol'] == 'admin':
        usuarios = db.query(Usuario).all()

    db.close()

    return render_template('welcome.html', usuario=user.username, rol=user.rol, usuarios=usuarios)



@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
