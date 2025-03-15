import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection(db_name='postgres'):
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=db_name,
            user=os.environ.get('DB_USER', 'nishant'),
            password=os.environ.get('DB_PASSWORD', 'nishant'),
            port=os.environ.get('DB_PORT', '5432')
        )
        conn.autocommit = True
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

def init_db():
    conn = get_db_connection('postgres')
    if conn is None:
        return

    cur = conn.cursor()

    db_name = os.environ.get('DB_NAME', 'codeanalyzer')
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f'CREATE DATABASE {db_name}')
        print(f"Database '{db_name}' Created.")
    else:
        print(f"Database '{db_name}' Already Exists.")

    cur.close()
    conn.close()

    conn = get_db_connection(db_name)
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'user',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("Users Table Created or Already Exists.")

    cur.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        language VARCHAR(50) NOT NULL,
        code TEXT NOT NULL,
        result JSONB NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("Analyses Table Created or Already Exists.")

    cur.execute('''
    INSERT INTO users (username, email, password_hash, role)
    VALUES ('demo', 'demo@example.com', 'pbkdf2:sha256:150000$abc123', 'user')
    ON CONFLICT (username) DO NOTHING
    ''')
    print("Demo User Created or Already Exists.")

    cur.close()
    conn.close()
    print("Database Initialization Complete.")

if __name__ == "__main__":
    init_db()
