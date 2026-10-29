"""
etl/export_csv.py – Export key tables to CSV and Excel in the output/ directory.
"""
import importlib.util, pathlib, pymysql
import pandas as pd

# Load config
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

OUTPUT_DIR = config.OUTPUT_DIR

def export():
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, charset='utf8mb4'
    )
    tables = ['Property', 'Development', 'Location', 'Developer', 'User']
    excel_path = OUTPUT_DIR / 'export.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for table in tables:
            try:
                df = pd.read_sql(f'SELECT * FROM `{table}`', conn)
                csv_path = OUTPUT_DIR / f'{table.lower()}.csv'
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                df.to_excel(writer, sheet_name=table, index=False)
                print(f"Exported {len(df)} rows from {table} -> {csv_path.name}")
            except Exception as e:
                print(f"Skipping {table}: {e}")
    conn.close()
    print(f"Excel export saved to {excel_path}")

if __name__ == '__main__':
    export()
