# main.py
from fastapi import FastAPI, HTTPException, Request, Depends, status, Security, Body
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from jose import JWTError, jwt
import csv
import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


CSV_PATH = 'List.csv'
templates = Jinja2Templates(directory="RESOURCES")

SECRET_KEY = os.getenv("SECRET_KEY")  # Load from .env file
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")  # Load from .env file
ADMIN_ALGORITHM = "HS256"
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
admin_oauth2_scheme = HTTPBearer()

# Initialize SQLite DB for users
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        brand TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS brand (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS country (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    conn.commit()
    conn.close()
init_db()

def get_user(username: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username, hashed_password, brand FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "hashed_password": row[1], "brand": row[2]}
    return None

def get_admin(username: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username, hashed_password FROM admin WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "hashed_password": row[1]}
    return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def authenticate_admin(username: str, password: str):
    admin = get_admin(username)
    if not admin or not verify_password(password, admin["hashed_password"]):
        return False
    return admin

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_admin_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(admin_oauth2_scheme)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = get_admin(username)
    if admin is None:
        raise credentials_exception
    return admin

# Helper: redirect unauthenticated users to /login
async def login_redirect_dependency(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or get_user(username) is None:
            raise Exception()
    except Exception:
        return RedirectResponse(url="/login")
    return token

@app.post("/register")
async def register(request: Request):
    form = await request.form()
    username = form.get('username')
    password = form.get('password')
    brand = form.get('brand')
    hashed_password = pwd_context.hash(password)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, hashed_password, brand) VALUES (?, ?, ?)', (username, hashed_password, brand))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    conn.close()
    return {"msg": "User registered successfully"}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "brand": user["brand"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer", "brand": user["brand"]}

@app.post("/admin_token")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = authenticate_admin(form_data.username, form_data.password)
    if not admin:
        raise HTTPException(status_code=400, detail="Incorrect admin username or password")
    access_token = create_admin_access_token(data={"sub": admin["username"]}, expires_delta=timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# Read CSV and cache file info
def read_csv():
    files = []
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            files.append({
                'name': row['Name'],
                'path': row['Path'],
                'version': row['Version'],
                'brand': row['Brand'],
                'category': row['Category'],
                'country': row['Country'],
            })
    return files

@app.get('/', response_class=HTMLResponse)
def select_brand(request: Request):
    with open("RESOURCES/select_brand.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get('/brand', response_class=HTMLResponse)
def list_files_by_brand(request: Request, brand: str):
    with open("RESOURCES/files_by_brand.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get('/files')
def list_files(user: dict = Depends(get_current_user)):
    return read_csv()

@app.get('/download/{name}')
def download_file(name: str, user: dict = Depends(get_current_user)):
    files = read_csv()
    file_info = next((f for f in files if f['name'] == name), None)
    if not file_info:
        raise HTTPException(status_code=404, detail='File not found')
    file_path = file_info['path']
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail='File not found on disk')
    # Use the original filename from the Path field
    original_filename = os.path.basename(file_path)
    base = os.path.join(os.path.dirname(os.path.abspath(CSV_PATH)), original_filename)
    return FileResponse(path=base, filename=original_filename, media_type='application/octet-stream')

@app.get('/register', response_class=HTMLResponse)
def serve_register():
    with open('RESOURCES/register.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/login', response_class=HTMLResponse)
def serve_login():
    with open('RESOURCES/login.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/admin_brand', response_class=HTMLResponse)
def serve_admin_brand():
    with open('RESOURCES/admin_brand.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/admin_login', response_class=HTMLResponse)
def serve_admin_login():
    return HTMLResponse("""
    <h1>Admin Login</h1>
    <form onsubmit=\"event.preventDefault();loginAdmin();\">
        <input type='text' name='username' placeholder='Username' required><br>
        <input type='password' name='password' placeholder='Password' required><br>
        <button type='submit'>Login</button>
    </form>
    <div id='msg'></div>
    <script>
    async function loginAdmin(){
        const form=document.forms[0];
        const data=new URLSearchParams();
        data.append('username',form.username.value);
        data.append('password',form.password.value);
        const res=await fetch('/admin_token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:data});
        const msg=document.getElementById('msg');
        if(res.ok){
            const result=await res.json();
            localStorage.setItem('admin_token',result.access_token);
            window.location.href='/admin_manage';
        }else{
            const err=await res.json();
            msg.textContent=err.detail||'Login failed.';
            msg.style.color='#d32f2f';
        }
    }
    </script>
    """)

@app.get('/admin_country', response_class=HTMLResponse)
def serve_admin_country():
    with open('RESOURCES/admin_country.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/admin_manage', response_class=HTMLResponse)
def serve_admin_manage():
    with open('RESOURCES/admin_brand_country.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/select_country', response_class=HTMLResponse)
def serve_select_country():
    with open('RESOURCES/select_country.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/files_by_brand', response_class=HTMLResponse)
def serve_files_by_brand(request: Request, brand: str = None, country: str = None):
    with open('RESOURCES/files_by_brand.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/api/brands')
def api_brands():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT name FROM brand ORDER BY name')
    brands = [row[0] for row in c.fetchall()]
    conn.close()
    return brands

@app.post('/api/brands')
def add_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Brand name required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO brand (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Brand already exists')
    conn.close()
    return {'msg': 'Brand added'}

@app.put('/api/brands')
def update_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail='Both old and new brand names required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE brand SET name=? WHERE name=?', (new_name, old_name))
    conn.commit()
    conn.close()
    return {'msg': 'Brand updated'}

@app.delete('/api/brands')
def delete_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Brand name required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM brand WHERE name=?', (name,))
    conn.commit()
    conn.close()
    return {'msg': 'Brand deleted'}

@app.get('/api/countries')
def api_countries():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT name FROM country ORDER BY name')
    countries = [row[0] for row in c.fetchall()]
    conn.close()
    return countries

@app.post('/api/countries')
def add_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Country name required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO country (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Country already exists')
    conn.close()
    return {'msg': 'Country added'}

@app.put('/api/countries')
def update_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail='Both old and new country names required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE country SET name=? WHERE name=?', (new_name, old_name))
    conn.commit()
    conn.close()
    return {'msg': 'Country updated'}

@app.delete('/api/countries')
def delete_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Country name required')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM country WHERE name=?', (name,))
    conn.commit()
    conn.close()
    return {'msg': 'Country deleted'}
