# export_products.py
import csv
from datetime import datetime
from pathlib import Path
import psycopg2
from db_config import DB_CONFIG


EXPORT_FOLDER="csv_files"

BASE_DIR = Path(__file__).resolve().parent
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT = BASE_DIR / EXPORT_FOLDER / f"products_export_{timestamp}.csv"

SQL = """
SELECT
    id, name, description, price, original_price,
    stock_quantity, sku, weight, rating,
    is_published, sell_count, brand_id, category_id,
    created_datetime, updated_datetime
FROM products_product
ORDER BY id;
"""

def export_products():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(SQL)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    
    # auto create dir  
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    cur.close()
    conn.close()
    print(f"Exported {len(rows)} rows -> {OUTPUT}")

if __name__ == "__main__":
    export_products()