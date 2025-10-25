# SITO.md - Documentazione Completa del Sistema GoliveLeo

## Indice
1. [Panoramica del Sistema](#panoramica-del-sistema)
2. [Casi d'Uso Pratici](#casi-duso-pratici)
3. [Funzionalità Utente](#funzionalità-utente)
4. [Funzionalità Amministratore](#funzionalità-amministratore)
5. [Architettura Tecnica](#architettura-tecnica)
6. [Configurazione e Deployment](#configurazione-e-deployment)
7. [Sicurezza](#sicurezza)
8. [Endpoint API Principali](#endpoint-api-principali)
9. [Esempi di Chiamate API](#esempi-di-chiamate-api)
10. [Dipendenze Principali](#dipendenze-principali)
11. [Note di Sviluppo](#note-di-sviluppo)
12. [Struttura File Repository](#struttura-file-repository)
13. [Supporto e Manutenzione](#supporto-e-manutenzione)

---

## Panoramica del Sistema

GoliveLeo è una piattaforma web di distribuzione file per strumenti diagnostici automotive. Il sistema gestisce l'accesso controllato a un catalogo di software diagnostici basato su brand automobilistici e paesi, con autenticazione utente e pannello amministrativo.

### Caratteristiche Principali
- **Controllo Accessi Granulare**: Filtraggio file per brand e paese
- **Autenticazione Dual-Mode**: Sistemi JWT separati per utenti e amministratori
- **Interfaccia Multilingua**: Supporto per 4 lingue (IT, FR, DE, ES)
- **Database PostgreSQL**: Scalabile e performante
- **API RESTful**: Endpoint moderni e ben documentati
- **Sicurezza Avanzata**: Password hashing, token JWT, validazione input

---

## Casi d'Uso Pratici

### Scenario 1: Tecnico Automotive che Accede ai File
1. Un tecnico della **BMW** visita `http://localhost:8000`
2. Si registra con username `tecnico_bmw`, password e seleziona brand "BMW"
3. Effettua il login e vede solo i file diagnostici BMW
4. Scarica il software diagnostico necessario per la diagnosi del veicolo
5. Il sistema verifica che abbia accesso solo ai file del brand BMW

### Scenario 2: Amministratore che Aggiunge un Nuovo Brand
1. L'admin accede a `http://localhost:8000/admin_login`
2. Inserisce le credenziali admin e ottiene il token JWT
3. Nella dashboard admin (`/admin_manage`) clicca su "Aggiungi Brand"
4. Inserisce "Tesla" come nuovo brand
5. Ora gli utenti possono registrarsi selezionando "Tesla" come brand

### Scenario 3: Distribuzione Internazionale
1. L'admin aggiunge paesi: Italia, Germania, Francia, Spagna
2. Il catalogo CSV (`List.csv`) contiene file specifici per ogni paese
3. Un utente in Italia seleziona paese "Italia" e vede solo file localizzati
4. Il sistema filtra automaticamente i file in base a brand + paese

---

## Funzionalità Utente

### 1. Registrazione e Autenticazione
- **Registrazione**: Gli utenti possono registrarsi fornendo username, password e brand di riferimento
- **Login**: Autenticazione tramite token JWT con durata di 30 minuti
- **Controllo Accessi**: Ogni utente ha accesso solo ai file del proprio brand assegnato

### 2. Catalogo File
- **Visualizzazione**: Interfaccia web per esplorare il catalogo file disponibili
- **Filtraggio Automatico**: I file vengono filtrati automaticamente in base al brand dell'utente
- **Metadati File**: Ogni file include:
  - Nome
  - Versione
  - Brand
  - Categoria
  - Paese
  - Path di download

### 3. Download File
- **Download Sicuro**: Download di file diagnostici autorizzati
- **Verifica Permessi**: Il sistema verifica che l'utente abbia accesso al file richiesto
- **Nome Originale**: I file vengono scaricati con il nome originale del filesystem

### 4. Interfaccia Multilingua
- Supporto per interfaccia in più lingue (Italiano, Francese, Tedesco, Spagnolo)
- Selezione brand e paese con interfaccia localizzata

---

## Funzionalità Amministratore

### 1. Autenticazione Admin
- **Login Separato**: Sistema di autenticazione dedicato per amministratori
- **Token JWT Admin**: Token con durata estesa di 60 minuti
- **Chiave Segreta Dedicata**: Utilizza una chiave JWT separata per maggiore sicurezza

### 2. Gestione Brand
- **Creazione**: Aggiungere nuovi brand al sistema
- **Modifica**: Rinominare brand esistenti
- **Eliminazione**: Rimuovere brand dal catalogo
- **Visualizzazione**: Elenco ordinato di tutti i brand disponibili

### 3. Gestione Paesi
- **Creazione**: Aggiungere nuovi paesi al sistema
- **Modifica**: Rinominare paesi esistenti
- **Eliminazione**: Rimuovere paesi dal catalogo
- **Visualizzazione**: Elenco ordinato di tutti i paesi disponibili

### 4. Pannello di Controllo
- **Interfaccia Web**: Dashboard amministrativa dedicata
- **API RESTful**: Endpoint protetti per tutte le operazioni CRUD
- **Protezione**: Tutte le operazioni richiedono autenticazione admin valida

---

## Architettura Tecnica

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL con connection pooling asincrono
- **ORM**: Database library asincrona per query PostgreSQL
- **Server**: Uvicorn ASGI server

### Autenticazione e Sicurezza
- **Password Hashing**: Bcrypt tramite passlib
- **Token JWT**: Due sistemi separati (utenti e admin)
- **Algoritmo**: HS256 per firma token
- **Scadenza Token**:
  - Utenti: 30 minuti
  - Admin: 60 minuti

### Database Schema
```
users:
  - id (SERIAL PRIMARY KEY)
  - username (TEXT UNIQUE)
  - hashed_password (TEXT)
  - brand (TEXT)

admin:
  - id (SERIAL PRIMARY KEY)
  - username (TEXT UNIQUE)
  - hashed_password (TEXT)

brand:
  - id (SERIAL PRIMARY KEY)
  - name (TEXT UNIQUE)

country:
  - id (SERIAL PRIMARY KEY)
  - name (TEXT UNIQUE)
```

### Catalogo File
- **Storage**: File CSV (`List.csv`)
- **Campi**: Name, Path, Version, Brand, Category, Country
- **Accesso**: Lettura in tempo reale del CSV per ogni richiesta
- **Filesystem**: File serviti direttamente dal filesystem locale

### Frontend
- **Template Engine**: Jinja2 per rendering HTML
- **Risorse**: Directory `RESOURCES/` con template HTML
- **JavaScript**: Client-side per autenticazione e chiamate API
- **Interfaccia**: Responsive e multilingua

---

## Configurazione e Deployment

### Variabili d'Ambiente Richieste

#### Per l'applicazione principale (main.py)
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=chiave_jwt_utenti_molto_sicura
ADMIN_SECRET_KEY=chiave_jwt_admin_molto_sicura
```

#### Per lo script di creazione admin (admin.py)
```bash
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=nome_database
PG_USER=postgres
PG_PASSWORD=password_postgres
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password_admin_sicura
```

**Nota**: Puoi creare un file `.env` nella root del progetto con tutte queste variabili.

### Guida Rapida all'Avvio

#### 1. Installazione Dipendenze
```bash
pip install -r requirements.txt
```

#### 2. Configurazione Database PostgreSQL
Assicurati di avere PostgreSQL installato e in esecuzione, poi crea un database:
```bash
psql -U postgres
CREATE DATABASE goliveleodb;
\q
```

#### 3. Configurazione File .env
Crea un file `.env` nella root del progetto:
```bash
# Database per l'applicazione
DATABASE_URL=postgresql://postgres:tuapassword@localhost:5432/goliveleodb

# Chiavi JWT (genera chiavi sicure casuali)
SECRET_KEY=genera_una_chiave_casuale_molto_lunga_e_sicura_123456
ADMIN_SECRET_KEY=genera_un_altra_chiave_casuale_diversa_dalla_prima_654321

# Configurazione PostgreSQL per admin.py
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=goliveleodb
PG_USER=postgres
PG_PASSWORD=tuapassword

# Credenziali primo admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password_admin_molto_sicura
```

#### 4. Creazione Primo Amministratore
```bash
python admin.py
```
Output atteso: `Admin aggiunto con successo!`

#### 5. Avvio Applicazione
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. Accesso all'Applicazione
- Interfaccia Utente: `http://localhost:8000`
- Login Admin: `http://localhost:8000/admin_login`
- Dashboard Admin: `http://localhost:8000/admin_manage`

### Inizializzazione Automatica
- Le tabelle del database vengono create automaticamente all'avvio tramite `init_db()` in main.py:243-271
- Non è necessaria alcuna configurazione manuale del database

### Migrazione da SQLite
Se hai un database SQLite esistente (`users.db`):
```bash
python migrate_sqlite_to_postgres.py
```
Questo script:
- Crea le tabelle in PostgreSQL se non esistono
- Copia tutti i dati da SQLite (users, admin, brand, country)
- Gestisce automaticamente i conflitti su chiavi duplicate

---

## Sicurezza

### Protezione Dati
- **Password**: Mai salvate in chiaro, solo hash bcrypt
- **Token**: Scadenza automatica per sessioni limitate
- **Separazione Ruoli**: Chiavi JWT separate per utenti e admin

### Controllo Accessi
- **Brand-Based Access**: Gli utenti vedono solo file del proprio brand
- **Admin Protection**: Endpoint admin protetti da autenticazione dedicata
- **File Verification**: Verifica esistenza file su filesystem prima del download

### Best Practices
- Uso di variabili d'ambiente per segreti
- ON CONFLICT per prevenire duplicati nel database
- Validazione input su tutti gli endpoint
- HTTPException per gestione errori standardizzata

---

## Endpoint API Principali

### Endpoint Pubblici
- `GET /` - Selezione brand
- `GET /login` - Pagina login utente
- `GET /register` - Pagina registrazione utente
- `GET /admin_login` - Pagina login admin

### Endpoint Utente (Autenticati)
- `POST /register` - Registrazione nuovo utente
- `POST /token` - Login e ottenimento JWT
- `GET /files` - Elenco file disponibili per il brand utente
- `GET /download/{name}` - Download file specifico
- `GET /brand?brand=X` - Visualizza file per brand
- `GET /select_country` - Selezione paese
- `GET /files_by_brand` - File filtrati per brand

### Endpoint Admin (Autenticati)
- `POST /admin_token` - Login admin e ottenimento JWT
- `GET /admin_manage` - Dashboard amministrativa
- `GET /api/brands` - Lista tutti i brand
- `POST /api/brands` - Crea nuovo brand
- `PUT /api/brands` - Modifica brand esistente
- `DELETE /api/brands` - Elimina brand
- `GET /api/countries` - Lista tutti i paesi
- `POST /api/countries` - Crea nuovo paese
- `PUT /api/countries` - Modifica paese esistente
- `DELETE /api/countries` - Elimina paese

---

## Esempi di Chiamate API

### Registrazione Utente
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tecnico_bmw&password=pass123&brand=BMW"
```

Risposta:
```json
{"msg": "User registered successfully"}
```

### Login Utente
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tecnico_bmw&password=pass123"
```

Risposta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "brand": "BMW"
}
```

### Ottenere Lista File (Autenticato)
```bash
curl -X GET http://localhost:8000/files \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Risposta:
```json
[
  {
    "name": "BMW Diagnostic Tool v2.5",
    "path": "/files/bmw/diagnostic_v2.5.exe",
    "version": "2.5.0",
    "brand": "BMW",
    "category": "Diagnostics",
    "country": "Italy"
  }
]
```

### Login Admin
```bash
curl -X POST http://localhost:8000/admin_token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin_password"
```

Risposta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Aggiungere Nuovo Brand (Admin)
```bash
curl -X POST http://localhost:8000/api/brands \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Tesla"}'
```

Risposta:
```json
{"msg": "Brand added"}
```

### Ottenere Lista Brand
```bash
curl -X GET http://localhost:8000/api/brands
```

Risposta:
```json
["Audi", "BMW", "Mercedes", "Tesla", "Volkswagen"]
```

### Modificare Brand (Admin)
```bash
curl -X PUT http://localhost:8000/api/brands \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"old_name": "Tesla", "new_name": "Tesla Motors"}'
```

Risposta:
```json
{"msg": "Brand updated"}
```

### Eliminare Brand (Admin)
```bash
curl -X DELETE http://localhost:8000/api/brands \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Tesla Motors"}'
```

Risposta:
```json
{"msg": "Brand deleted"}
```

---

## Dipendenze Principali

- **fastapi** - Framework web
- **uvicorn** - ASGI server
- **databases** - Async database support
- **asyncpg** - PostgreSQL async driver
- **passlib** - Password hashing
- **python-jose** - JWT token management
- **pydantic** - Data validation
- **starlette** - ASGI toolkit

---

## Note di Sviluppo

### Migrazione PostgreSQL
Il sistema è stato migrato da SQLite a PostgreSQL per:
- Migliore scalabilità
- Connection pooling
- Supporto concorrenza
- Compatibilità production

### Prossimi Sviluppi Suggeriti
- Implementazione cache per `List.csv`
- Logging strutturato per audit trail
- Rate limiting su endpoint pubblici
- Backup automatico database
- Health check endpoint
- Metrics e monitoring
- Upload file tramite interfaccia admin
- Gestione versioni file
- Notifiche email per nuovi file

---

## Struttura File Repository

```
/
├── main.py                          # Applicazione FastAPI principale
├── admin.py                         # Script creazione admin
├── migrate_sqlite_to_postgres.py   # Script migrazione database
├── debug_bcrypt.py                  # Utility debug bcrypt
├── List.csv                         # Catalogo file
├── requirements.txt                 # Dipendenze Python
├── .env                            # Variabili d'ambiente (non in repo)
├── .gitignore                       # File da ignorare in git
├── CLAUDE.md                        # Istruzioni per Claude Code
├── README.md                        # Documentazione setup
├── SECURITY.md                      # Policy di sicurezza
├── SITO.md                          # Questo file - Documentazione funzionalità
└── RESOURCES/
    ├── select_brand.html           # Selezione brand
    ├── select_country.html         # Selezione paese
    ├── login.html                  # Login utente
    ├── register.html               # Registrazione utente
    ├── files_by_brand.html         # Elenco file per brand
    ├── admin_brand.html            # Gestione brand
    ├── admin_country.html          # Gestione paesi
    ├── admin_brand_country.html    # Dashboard admin
    └── translations_example.html   # Esempio traduzioni
```

---

## Supporto e Manutenzione

Per questioni tecniche o miglioramenti, fare riferimento a:
- **CLAUDE.md** - Linee guida sviluppo con Claude Code
- **README.md** - Setup e configurazione
- **SECURITY.md** - Policy di sicurezza

---

*Documento generato il 2025-10-25*
