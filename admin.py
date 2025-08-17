import os
import sys
from dotenv import load_dotenv
import psycopg2
from passlib.context import CryptContext
import types
try:
    import bcrypt
except Exception:
    bcrypt = None

# compat shim: alcune versioni di passlib cercano `bcrypt.__about__.__version__`.
# Il pacchetto `bcrypt` moderno espone `__version__` ma non `__about__`.
if bcrypt is not None and not hasattr(bcrypt, "__about__"):
    setattr(bcrypt, "__about__", types.SimpleNamespace(__version__=getattr(bcrypt, "__version__", "<unknown>")))

# Carica le variabili d'ambiente dal file .env nella root del progetto
load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Preferibile usare variabili d'ambiente in produzione; nessun valore di default fornito
username = os.getenv("ADMIN_USERNAME")
password = os.getenv("ADMIN_PASSWORD")

# Verifica che le variabili essenziali siano impostate
required = [
    "PG_HOST",
    "PG_PORT",
    "PG_DATABASE",
    "PG_USER",
    "PG_PASSWORD",
    "ADMIN_USERNAME",
    "ADMIN_PASSWORD",
]
missing = [v for v in required if not os.getenv(v)]
if missing:
    print("Variabili d'ambiente mancanti:", ", ".join(missing))
    sys.exit(1)

hashed_password = pwd_context.hash(password)

conn = None
cur = None
try:
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )

    cur = conn.cursor()
    # Assicura che la tabella esista
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )
    """)
    # Inserisce o aggiorna la password se l'username esiste già
    cur.execute(
        "INSERT INTO admin (username, hashed_password) VALUES (%s, %s) ON CONFLICT (username) DO UPDATE SET hashed_password = EXCLUDED.hashed_password",
        (username, hashed_password),
    )
    conn.commit()
    print("Admin aggiunto con successo!")
except Exception as e:
    print("Errore durante l'operazione sul DB:", e)
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()