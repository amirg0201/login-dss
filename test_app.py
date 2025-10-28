import pytest
# Importa tu aplicación Flask y la configuración de la BD
import app as flask_app
from database import init_db, SessionLocal, engine
from models.user import Usuario
from app import app
from models.user import Base

@pytest.fixture
def client():
  # 1. Configurar la app para modo "testing"
  app.config['TESTING'] = True
  app.config['WTF_CSRF_ENABLED'] = False # Deshabilita CSRF para pruebas

  # 2. Establecer el cliente de pruebas y el contexto de la app
  with app.app_context():
      
    # 3. CREAR UNA BASE DE DATOS LIMPIA
    # Borra todas las tablas existentes usando los metadatos de 'Base'
    Base.metadata.drop_all(bind=engine) 
      
    # Vuelve a crear el esquema desde cero
    init_db()

    # 4. Entregar (yield) el cliente de pruebas
    # La prueba se ejecuta aquí.
    yield app.test_client() 

    # 5. Limpieza (se ejecuta DESPUÉS de que la prueba termine)
    Base.metadata.drop_all(bind=engine)


# --- Pruebas de Rutas (GET) ---

def test_index_redirects_to_login(client):
  """Prueba que la ruta raíz '/' redirige a '/login'."""
  response = client.get('/')
  # 302 es el código HTTP para "Redirección"
  assert response.status_code == 302
  assert '/login' in response.location

def test_login_page_loads(client):
  """Prueba que la página de login carga correctamente."""
  response = client.get('/login')
  assert response.status_code == 200
  assert b"Login" in response.data # Asume que tu HTML tiene la palabra "Login"

def test_register_page_loads(client):
  """Prueba que la página de registro carga correctamente."""
  response = client.get('/register')
  assert response.status_code == 200
  assert b"Registro" in response.data # Asume que tu HTML tiene la palabra "Registro"

def test_welcome_page_redirects_if_not_logged_in(client):
  """Prueba que '/welcome' redirige a '/login' si no hay sesión."""
  response = client.get('/welcome')
  assert response.status_code == 302
  assert '/login' in response.location

# --- Pruebas de Lógica de Usuario (POST) ---

def test_successful_registration(client):
  """Prueba el registro exitoso de un nuevo usuario."""
  # follow_redirects=True sigue la redirección al login
  response = client.post('/register', data={
    'username': 'testuser',
    'password': 'password123',
    'rol': 'user'
  }, follow_redirects=True)
  
  # 1. Debería terminar en la página de login
  assert response.status_code == 200
  assert b"Login" in response.data 

  # 2. Verifica que el usuario SÍ se creó en la BD
  db = SessionLocal()
  user = db.query(Usuario).filter_by(username='testuser').first()
  db.close()
  assert user is not None
  assert user.rol == 'user'

def test_duplicate_registration_fails(client):
  """Prueba que no se puede registrar un usuario con el mismo nombre."""
  # 1. Registra el primer usuario
  client.post('/register', data={
    'username': 'testuser', 'password': '123', 'rol': 'user'
  })
  
  # 2. Intenta registrarlo de nuevo
  response = client.post('/register', data={
    'username': 'testuser', 'password': '456', 'rol': 'admin'
  })
  
  assert response.status_code == 200
  assert b"Usuario ya registrado." in response.data

def test_login_invalid_credentials(client):
  """Prueba el login con credenciales incorrectas."""
  response = client.post('/login', data={
    'username': 'nouser', 'password': 'nopass'
  })
  assert response.status_code == 200
  assert b"Credenciales incorrectas" in response.data

def test_login_and_welcome_page(client):
  """Prueba un ciclo de login exitoso y la página de bienvenida."""
  # 1. Registrar un usuario primero
  client.post('/register', data={
    'username': 'welcomeuser', 'password': 'welcomepass', 'rol': 'user'
  })
  
  # 2. Iniciar sesión con ese usuario
  response = client.post('/login', data={
    'username': 'welcomeuser',
    'password': 'welcomepass'
  }, follow_redirects=True)
  
  # 3. Verificar que llegamos a la página de bienvenida
  assert response.status_code == 200
  # Asumimos que welcome.html muestra el nombre y rol
  assert b"welcomeuser" in response.data 
  assert b"Tu rol es: user" in response.data
  
  # 4. Verificar que NO vemos la lista de admin
  assert b"usuarios=" not in response.data

# --- Pruebas de Lógica de Admin ---

def test_admin_sees_user_list(client):
  """Prueba que un 'admin' ve la lista de usuarios en /welcome."""
  # 1. Registrar un usuario normal
  client.post('/register', data={
    'username': 'normaluser', 'password': '123', 'rol': 'user'
  })
  
  # 2. Registrar un usuario admin
  client.post('/register', data={
    'username': 'admin', 'password': 'adminpass', 'rol': 'admin'
  })
  
  # 3. Iniciar sesión como admin
  response = client.post('/login', data={
    'username': 'admin',
    'password': 'adminpass'
  }, follow_redirects=True)
  
  # 4. Verificar que el admin ve la bienvenida y su rol
  assert response.status_code == 200
  assert b"Tu rol es: admin" in response.data
  
  # 5. Verificar que el admin ve al "normaluser" en la lista
  # (Tu app pasa la variable 'usuarios' a la plantilla)
  # assert b"usuarios=" in response.data
  assert b"normaluser" in response.data 

# --- Pruebas de Sesión (Logout) ---

def test_logout(client):
  """Prueba el ciclo completo: registro, login, logout y verificación."""
  # 1. Registrar y hacer login
  client.post('/register', data={
    'username': 'logoutuser', 'password': '123', 'rol': 'user'
  })
  client.post('/login', data={
    'username': 'logoutuser', 'password': '123'
  })
  
  # 2. Verificar que estamos logueados (podemos ver /welcome)
  response_welcome = client.get('/welcome')
  assert response_welcome.status_code == 200
  
  # 3. Hacer logout
  response_logout = client.get('/logout')
  assert response_logout.status_code == 302 # Redirige al login
  assert '/login' in response_logout.location
  
  # 4. Verificar que ya NO estamos logueados
  response_welcome_after = client.get('/welcome')
  assert response_welcome_after.status_code == 302 # Redirige al login