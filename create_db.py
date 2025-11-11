#!/usr/bin/env python3
"""
create_db.py

Utility to create the PostgreSQL database (if missing) using DB_* env vars
and then create tables via SQLAlchemy's db.create_all() for local development.

Usage:
    & .\.venv\Scripts\Activate.ps1
    python src/backend/create_db.py

This script will:
- load `src/backend/.env` (dotenv)
- build a postgres DSN from DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME
- attempt to connect to the server and create the database if it doesn't exist
- set DATABASE_URL in the process environment and call the application's
  create_app() + db.create_all() to create tables.

Note: This is a dev convenience: in production prefer migrations (alembic/flask-migrate).
"""
import os
import sys
from dotenv import load_dotenv

# ensure we load the project's .env (located next to this script)
HERE = os.path.dirname(__file__)
DOTENV_PATH = os.path.join(HERE, '.env')
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    # fall back to loading from current environment
    load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    print('Missing one or more DB_* environment variables in .env. Aborting.')
    print('Please set DB_USER, DB_PASSWORD, DB_HOST, DB_PORT and DB_NAME.')
    sys.exit(1)

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print('Using database URL:', DB_URL)

# Try to create the Postgres database if it doesn't exist
try:
    import psycopg2
    from psycopg2 import sql
    # connect to default administrative DB 'postgres' to create the target DB
    admin_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    conn = psycopg2.connect(admin_dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (DB_NAME,))
    exists = cur.fetchone()
    if not exists:
        print(f"Database '{DB_NAME}' not found — creating...")
        cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DB_NAME)))
        print('Database created successfully.')
    else:
        print(f"Database '{DB_NAME}' already exists.")
    cur.close()
    conn.close()
except Exception as e:
    print('Warning: could not create/check PostgreSQL database. Error:')
    print(e)
    print('\nYou can create the database manually or ensure the DB server is running and credentials are correct.')
    # continue: we will still attempt create_all (it may fail if DB unreachable)

# Set DATABASE_URL for the application runtime (so create_app picks it up)
os.environ['DATABASE_URL'] = DB_URL

# Import the app factory and DB and create tables
try:
    # Import here so that we use the project's app package
    from app import create_app, db

    app = create_app()
    with app.app_context():
        print('Creating tables with db.create_all()...')
        db.create_all()
        print('Tables created (or already present).')
except Exception as e:
    print('Error while initializing app or creating tables:')
    print(e)
    print('\nIf this is a psycopg2 encoding/DSN error, verify that your .env is UTF-8 and that DATABASE_URL (if present) is a plain expanded DSN without ${...} placeholders.')
    sys.exit(1)
