import pymysql, os, pathlib, sys
from pathlib import Path

# Load config (same dynamic method as other scripts)
import importlib.util
config_path = Path(__file__).resolve().parent / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_NAME = config.DB_NAME
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD

schema_file = Path(__file__).parent / 'schema.sql'
if not schema_file.is_file():
    print('Schema file not found:', schema_file)
    sys.exit(1)

with open(schema_file, 'r', encoding='utf-8') as f:
    sql = f.read()

# Connect to MySQL server (no database yet) to create DB if needed
conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, autocommit=True)
try:
    with conn.cursor() as cur:
        # Create database if not exists
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Database `{DB_NAME}` ensured.")
    conn.select_db(DB_NAME)
    # Split statements by ';' handling multiline; simple split is okay for this schema
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    with conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt + ';')
            except Exception as e:
                print('Error executing statement:', stmt)
                print(e)
    print('Schema applied successfully.')
finally:
    conn.close()

