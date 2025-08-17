# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Flusso di lavoro standard
1. Per prima cosa, analizza il problema, cerca i file rilevanti nel codice e scrivi un piano per todo.md. 2. Il piano dovrebbe contenere una lista di cose da fare che puoi spuntare man mano che le completi.
3. Prima di iniziare a lavorare, contattami e verificherò il piano.
4. Quindi, inizia a lavorare sulle cose da fare, contrassegnandole come completate man mano che procedi.
5. Per favore, per ogni passaggio, forniscimi una spiegazione dettagliata delle modifiche apportate.
6. Semplifica il più possibile ogni attività e modifica al codice. Vogliamo evitare modifiche massicce o complesse. Ogni modifica dovrebbe avere un impatto minimo sul codice. Tutto ruota intorno alla semplicità.
7. Infine, aggiungi una sezione di revisione al file todo.md con un riepilogo delle modifiche apportate e qualsiasi altra informazione pertinente.

## Project Overview

This is a FastAPI-based file distribution system for automotive diagnostic tools. The application manages user authentication, brand/country-based file access, and admin controls for a catalog of diagnostic software files.

## Key Architecture Components

### Main Application (`main.py`)
- FastAPI web server with dual authentication systems:
  - User authentication with brand-based access control
  - Admin authentication for brand/country management
- SQLite database for users, admins, brands, and countries
- File serving from CSV catalog (`List.csv`)
- JWT token authentication with separate keys for users and admins

### Database Schema
- `users` table: id, username, hashed_password, brand
- `admin` table: id, username, hashed_password  
- `brand` table: id, name
- `country` table: id, name

### File Structure
- `RESOURCES/` - HTML templates for web interface
- `List.csv` - File catalog with columns: Name, Path, Version, Brand, Category, Country
- `users.db` - SQLite database (auto-created)
- `translations.js` - Multi-language support (Italian, French, German, Spanish)
- `admin.py` - Script to create admin users

## Development Commands

### Running the Application
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Database Setup
- Database initializes automatically on first run via `init_db()`
- To create admin user: `python admin.py`

### Environment Variables Required
- `SECRET_KEY` - JWT secret for user tokens
- `ADMIN_SECRET_KEY` - JWT secret for admin tokens

## Authentication Flow

### User Authentication
1. Register at `/register` with username, password, brand
2. Login at `/token` returns JWT with brand info
3. Access files filtered by user's brand

### Admin Authentication  
1. Login at `/admin_token` 
2. Manage brands/countries via `/api/brands` and `/api/countries` endpoints
3. CRUD operations protected by admin JWT

## File Access Control
- Users can only download files matching their assigned brand
- File metadata served from CSV, actual files served from filesystem paths
- Brand-based filtering applied to file listings
