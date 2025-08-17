"""Migration script: copies users, admin, brand, country from local SQLite `users.db` into Postgres using DATABASE_URL.

Usage:
  python migrate_sqlite_to_postgres.py

Requires: environment variable DATABASE_URL set or .env file with it.

Notes:
- It will create tables in Postgres (id as SERIAL) if they don't exist.
- It will copy rows and preserve usernames and hashed_passwords and brand.
- It skips duplicate usernames/names when inserting (Postgres unique constraint).
"""
import os
import sqlite3
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

SQLITE_DB = 'users.db'
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL not set in environment')

def read_sqlite_table(table_name):
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def migrate():
    # Connect to Postgres
    pg = psycopg2.connect(DATABASE_URL)
    try:
        with pg.cursor() as c:
            # Ensure tables exist
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                brand TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS admin (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS brand (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS country (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')
        pg.commit()

        # Migrate users
        users = read_sqlite_table('users')
        if users:
            tuples = [(u['username'], u['hashed_password'], u.get('brand')) for u in users]
            with pg.cursor() as c:
                execute_values(c,
                    "INSERT INTO users (username, hashed_password, brand) VALUES %s ON CONFLICT (username) DO NOTHING",
                    tuples)
            pg.commit()
            print(f"Migrated {len(tuples)} users")

        # Migrate admin
        admins = read_sqlite_table('admin')
        if admins:
            tuples = [(a['username'], a['hashed_password']) for a in admins]
            with pg.cursor() as c:
                execute_values(c,
                    "INSERT INTO admin (username, hashed_password) VALUES %s ON CONFLICT (username) DO NOTHING",
                    tuples)
            pg.commit()
            print(f"Migrated {len(tuples)} admins")

        # Migrate brand
        brands = read_sqlite_table('brand')
        if brands:
            tuples = [(b['name'],) for b in brands]
            with pg.cursor() as c:
                execute_values(c,
                    "INSERT INTO brand (name) VALUES %s ON CONFLICT (name) DO NOTHING",
                    tuples)
            pg.commit()
            print(f"Migrated {len(tuples)} brands")

        # Migrate country
        countries = read_sqlite_table('country')
        if countries:
            tuples = [(c['name'],) for c in countries]
            with pg.cursor() as c:
                execute_values(c,
                    "INSERT INTO country (name) VALUES %s ON CONFLICT (name) DO NOTHING",
                    tuples)
            pg.commit()
            print(f"Migrated {len(tuples)} countries")

    finally:
        pg.close()

if __name__ == '__main__':
    migrate()
