# main.py
from fastapi import FastAPI, HTTPException, Request, Depends, status, Security, Body
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
import csv
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv
from databases import Database
from urllib.parse import urlparse

load_dotenv()

app = FastAPI()

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

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # We'll let startup raise if DB isn't provided; keep variable for syntax
    DATABASE_URL = None

database = Database(DATABASE_URL) if DATABASE_URL else None


async def init_db():
    """Create tables if missing using the async database connection."""
    await database.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        brand TEXT
    )
    ''')
    await database.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )
    ''')
    await database.execute('''
    CREATE TABLE IF NOT EXISTS brand (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    await database.execute('''
    CREATE TABLE IF NOT EXISTS country (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    ''')


@app.on_event('startup')
async def startup_event():
    global database
    if DATABASE_URL is None:
        raise RuntimeError('DATABASE_URL not set in environment')
    database = Database(DATABASE_URL)
    await database.connect()
    await init_db()


@app.on_event('shutdown')
async def shutdown_event():
    if database is not None:
        await database.disconnect()

async def get_user(username: str):
    row = await database.fetch_one(
        "SELECT username, hashed_password, brand FROM users WHERE username = :username",
        {"username": username}
    )
    if row:
        return {"username": row["username"], "hashed_password": row["hashed_password"], "brand": row["brand"]}
    return None


async def get_admin(username: str):
    row = await database.fetch_one(
        "SELECT username, hashed_password FROM admin WHERE username = :username",
        {"username": username}
    )
    if row:
        return {"username": row["username"], "hashed_password": row["hashed_password"]}
    return None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user


async def authenticate_admin(username: str, password: str):
    admin = await get_admin(username)
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
        if username is None or await get_user(username) is None:
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
    row = await database.fetch_one(
        """
        INSERT INTO users (username, hashed_password, brand)
        VALUES (:username, :hashed_password, :brand)
        ON CONFLICT (username) DO NOTHING
        RETURNING id
        """,
        {"username": username, "hashed_password": hashed_password, "brand": brand}
    )
    if not row:
        raise HTTPException(status_code=400, detail="Username already registered")
    return {"msg": "User registered successfully"}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "brand": user["brand"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer", "brand": user["brand"]}

@app.post("/admin_token")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = await authenticate_admin(form_data.username, form_data.password)
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
    return FileResponse(path=file_path, filename=original_filename, media_type='application/octet-stream')

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
def serve_files_by_brand(request: Request, country: str = None):
    with open('RESOURCES/files_by_brand.html', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/api/brands')
async def api_brands():
    rows = await database.fetch_all('SELECT name FROM brand ORDER BY name')
    return [r['name'] for r in rows]

@app.post('/api/brands')
async def add_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Brand name required')
    row = await database.fetch_one(
        "INSERT INTO brand (name) VALUES (:name) ON CONFLICT (name) DO NOTHING RETURNING id",
        {"name": name}
    )
    if not row:
        raise HTTPException(status_code=400, detail='Brand already exists')
    return {'msg': 'Brand added'}

@app.put('/api/brands')
async def update_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail='Both old and new brand names required')
    await database.execute('UPDATE brand SET name = :new_name WHERE name = :old_name', {"new_name": new_name, "old_name": old_name})
    return {'msg': 'Brand updated'}

@app.delete('/api/brands')
async def delete_brand(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Brand name required')
    await database.execute('DELETE FROM brand WHERE name = :name', {"name": name})
    return {'msg': 'Brand deleted'}

@app.get('/api/countries')
async def api_countries():
    rows = await database.fetch_all('SELECT name FROM country ORDER BY name')
    return [r['name'] for r in rows]

@app.post('/api/countries')
async def add_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Country name required')
    row = await database.fetch_one(
        "INSERT INTO country (name) VALUES (:name) ON CONFLICT (name) DO NOTHING RETURNING id",
        {"name": name}
    )
    if not row:
        raise HTTPException(status_code=400, detail='Country already exists')
    return {'msg': 'Country added'}

@app.put('/api/countries')
async def update_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail='Both old and new country names required')
    await database.execute('UPDATE country SET name = :new_name WHERE name = :old_name', {"new_name": new_name, "old_name": old_name})
    return {'msg': 'Country updated'}

@app.delete('/api/countries')
async def delete_country(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    name = data.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='Country name required')
    await database.execute('DELETE FROM country WHERE name = :name', {"name": name})
    return {'msg': 'Country deleted'}
