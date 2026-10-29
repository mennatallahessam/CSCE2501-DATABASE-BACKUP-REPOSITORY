import importlib.util, pathlib, json
import pymysql
from pathlib import Path

# Load configuration from project root (two levels up)
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_NAME = config.DB_NAME
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        autocommit=False,
    )

# ---- Helper functions ----
def ensure_lookup(conn, table, name_col, name):
    """Simple lookup/insert for tables with a single unique name column (e.g., Developer)."""
    select_sql = f"SELECT {table.lower()}_id FROM {table} WHERE {name_col}=%s"
    insert_sql = f"INSERT INTO {table} ({name_col}) VALUES (%s)"
    with conn.cursor() as cur:
        cur.execute(select_sql, (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(insert_sql, (name,))
        return cur.lastrowid

def ensure_location(conn, city, district, area):
    select_sql = "SELECT location_id FROM Location WHERE city=%s AND district=%s AND area=%s"
    insert_sql = "INSERT INTO Location (city, district, area) VALUES (%s, %s, %s)"
    with conn.cursor() as cur:
        cur.execute(select_sql, (city, district, area))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(insert_sql, (city, district, area))
        return cur.lastrowid

def ensure_development(conn, name, location_id, developer_id):
    """Get or create a Development row using name + location + developer."""
    select_sql = "SELECT development_id FROM Development WHERE name=%s AND location_id=%s"
    insert_sql = "INSERT INTO Development (name, location_id, developer_id) VALUES (%s, %s, %s)"
    with conn.cursor() as cur:
        cur.execute(select_sql, (name, location_id))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(insert_sql, (name, location_id, developer_id))
        return cur.lastrowid

# ---- Property upsert ----
def upsert_property(conn, rec):
    sql = """
    INSERT INTO Property (
        url, title, description, asking_price, market_price, area_sqm,
        bedrooms, bathrooms, property_type, floor, finishing,
        contract_year, down_payment, payment_method, gain_over_market,
        development_id, location_id
    ) VALUES (
        %(url)s, %(title)s, %(description)s, %(asking_price)s, %(market_price)s, %(area_sqm)s,
        %(bedrooms)s, %(bathrooms)s, %(property_type)s, %(floor)s, %(finishing)s,
        %(contract_year)s, %(down_payment)s, %(payment_method)s, %(gain_over_market)s,
        %(development_id)s, %(location_id)s
    ) ON DUPLICATE KEY UPDATE
        title=VALUES(title), description=VALUES(description), asking_price=VALUES(asking_price),
        market_price=VALUES(market_price), area_sqm=VALUES(area_sqm), bedrooms=VALUES(bedrooms),
        bathrooms=VALUES(bathrooms), property_type=VALUES(property_type), floor=VALUES(floor),
        finishing=VALUES(finishing), contract_year=VALUES(contract_year), down_payment=VALUES(down_payment),
        payment_method=VALUES(payment_method), gain_over_market=VALUES(gain_over_market),
        development_id=VALUES(development_id), location_id=VALUES(location_id);
    """
    with conn.cursor() as cur:
        cur.execute(sql, rec)

# ---- Main loader ----
def load():
    cleaned_path = Path(__file__).parents[2] / 'cleaned.jsonl'
    conn = get_connection()
    try:
        with open(cleaned_path, 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                # 1) Ensure Location
                loc_id = ensure_location(
                    conn,
                    rec.get('city') or 'Sample City',
                    rec.get('district') or 'Sample District',
                    rec.get('area') or 'Sample Area',
                )
                # 2) Ensure Developer (dummy if not present)
                dev_dev_id = ensure_lookup(
                    conn,
                    'Developer',
                    'name',
                    rec.get('developer_name') or 'Sample Developer',
                )
                # 3) Ensure Development using name, location, developer
                dev_id = None
                if rec.get('development_name'):
                    dev_id = ensure_development(
                        conn,
                        rec['development_name'],
                        loc_id,
                        dev_dev_id,
                    )
                # 4) Attach foreign keys to record
                rec.update({
                    'development_id': dev_id,
                    'location_id': loc_id,
                })
                # Debug output
                print('Prepared record for insert:', rec)
                upsert_property(conn, rec)
        conn.commit()
        print('Load completed successfully.')
    except Exception as e:
        conn.rollback()
        print('Error during load:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    load()
