import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
username = "SuperUser"  # Sostituisci con il nome utente desiderato
password = "VivaParma12@"  # Sostituisci con la password desiderata
hashed_password = pwd_context.hash(password)

conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('INSERT INTO admin (username, hashed_password) VALUES (?, ?)', (username, hashed_password))
conn.commit()
conn.close()
print("Admin aggiunto con successo!")