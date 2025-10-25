# SITO.md

## Panoramica del Sistema

GoliveLeo è una piattaforma web di distribuzione file per strumenti diagnostici automotive. Il sistema gestisce l'accesso controllato a un catalogo di software diagnostici basato su brand automobilistici e paesi, con autenticazione utente e pannello amministrativo.

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
```
DATABASE_URL=postgres://user:password@host:5432/dbname
SECRET_KEY=chiave_jwt_utenti
ADMIN_SECRET_KEY=chiave_jwt_admin
DB_MIN_CONN=1 (opzionale)
DB_MAX_CONN=10 (opzionale)
```

### Installazione
```bash
pip install -r requirements.txt
```

### Avvio Applicazione
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Inizializzazione Database
- Le tabelle vengono create automaticamente all'avvio tramite `init_db()`
- Per creare un utente admin: `python admin.py`

### Migrazione da SQLite
- Script disponibile: `migrate_sqlite_to_postgres.py`
- Migra dati esistenti da `users.db` a PostgreSQL

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
├── List.csv                         # Catalogo file
├── requirements.txt                 # Dipendenze Python
├── .env                            # Variabili d'ambiente (non in repo)
├── CLAUDE.md                        # Istruzioni per Claude Code
├── README.md                        # Documentazione setup
├── SECURITY.md                      # Policy di sicurezza
├── SITO.md                          # Questo file
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
