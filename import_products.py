# import_products.py
import argparse
import csv
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from db_config import DB_CONFIG

BASE_DIR = Path(__file__).resolve().parent


def clean_val(val):
    """Convert empty strings to None (SQL NULL) and strip whitespaces."""
    if val is None or val.strip() == "":
        return None
    return val.strip()


def get_existing_skus(cur):
    """Fetch all SKUs currently in the database into a set for fast lookup."""
    cur.execute("SELECT sku FROM products_product WHERE sku IS NOT NULL;")
    return {row[0] for row in cur.fetchall()}


def generate_unique_sku(base_sku, existing_skus):
    """Generate a guaranteed unique SKU if base_sku already exists."""
    if base_sku not in existing_skus:
        existing_skus.add(base_sku)
        return base_sku

    # If SKU exists, append _1, _2, _3... until unique
    counter = 1
    new_sku = f"{base_sku}_{counter}"
    while new_sku in existing_skus:
        counter += 1
        new_sku = f"{base_sku}_{counter}"

    existing_skus.add(new_sku)
    return new_sku


def import_products(csv_path):
    target_file = Path(csv_path)
    if not target_file.exists():
        print(f"Error: File not found -> {target_file}")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # 1. Reset ID sequence so next insert starts from MAX(id) + 1
        sync_seq_sql = """
        SELECT setval(
            pg_get_serial_sequence('products_product', 'id'),
            COALESCE((SELECT MAX(id) FROM products_product), 0)
        );
        """
        cur.execute(sync_seq_sql)

        # 2. Fetch existing SKUs from DB to prevent collisions
        existing_skus = get_existing_skus(cur)

        valid_tuples = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(target_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = clean_val(row.get("name"))
                raw_sku = clean_val(row.get("sku")) or "SKU-AUTO"

                if not name:
                    continue  # Skip rows without name

                # Make SKU unique across DB and current CSV batch
                unique_sku = generate_unique_sku(raw_sku, existing_skus)

                tup = (
                    name,
                    clean_val(row.get("description")),
                    float(row["price"]) if clean_val(row.get("price")) else 0.0,
                    (
                        float(row["original_price"])
                        if clean_val(row.get("original_price"))
                        else 0.0
                    ),
                    (
                        int(row["stock_quantity"])
                        if clean_val(row.get("stock_quantity"))
                        else 0
                    ),
                    unique_sku,
                    (
                        float(row["weight"])
                        if clean_val(row.get("weight"))
                        else 0.0
                    ),
                    (
                        float(row["rating"])
                        if clean_val(row.get("rating"))
                        else 0.0
                    ),
                    (
                        clean_val(row.get("is_published", "")).lower()
                        in ("true", "1", "t")
                    ),
                    (
                        int(row["sell_count"])
                        if clean_val(row.get("sell_count"))
                        else 0
                    ),
                    (
                        int(row["brand_id"])
                        if clean_val(row.get("brand_id"))
                        else None
                    ),
                    (
                        int(row["category_id"])
                        if clean_val(row.get("category_id"))
                        else None
                    ),
                    clean_val(row.get("created_datetime")) or now_str,
                    clean_val(row.get("updated_datetime")) or now_str,
                )
                valid_tuples.append(tup)

        if not valid_tuples:
            print("No valid rows found in CSV.")
            return

        # 3. Direct INSERT into database (no conflict errors because SKUs are unique)
        insert_sql = """
        INSERT INTO products_product (
            name, description, price, original_price,
            stock_quantity, sku, weight, rating,
            is_published, sell_count, brand_id, category_id,
            created_datetime, updated_datetime
        ) VALUES %s;
        """

        execute_values(cur, insert_sql, valid_tuples)
        conn.commit()

        print(
            f"Successfully inserted {len(valid_tuples)} new product records with unique SKUs!"
        )

    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import CSV products forcing unique SKUs and incremental IDs."
    )
    parser.add_argument("csv_path", type=str, help="Path to CSV file")
    args = parser.parse_args()
    import_products(args.csv_path)