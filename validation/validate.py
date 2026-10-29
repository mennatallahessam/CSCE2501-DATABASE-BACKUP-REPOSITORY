"""
validation/validate.py – Run basic integrity checks on the database.
"""
import importlib.util, pathlib, pymysql, sys

# Load config
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

CHECKS = [
    ("Property rows",         "SELECT COUNT(*) FROM Property"),
    ("Properties with price", "SELECT COUNT(*) FROM Property WHERE asking_price IS NOT NULL"),
    ("Orphan properties",     "SELECT COUNT(*) FROM Property WHERE development_id NOT IN (SELECT development_id FROM Development)"),
    ("User rows",             "SELECT COUNT(*) FROM `User`"),
    ("Location rows",         "SELECT COUNT(*) FROM Location"),
    ("Developer rows",        "SELECT COUNT(*) FROM Developer"),
    ("Development rows",      "SELECT COUNT(*) FROM Development"),
]

def validate():
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, charset='utf8mb4'
    )
    all_passed = True
    print("\n=== Validation Report ===")
    with conn.cursor() as cur:
        for label, sql in CHECKS:
            cur.execute(sql)
            result = cur.fetchone()[0]
            status = '[OK]' if result >= 0 else '[FAIL]'
            if label == "Orphan properties" and result > 0:
                status = 'FAIL'
                all_passed = False
            print(f"  [{status}]  {label}: {result}")
    conn.close()
    print("=== " + ("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED") + " ===\n")
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    validate()
