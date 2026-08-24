import os
import shutil
from pathlib import Path
import random
import psycopg2
from decimal import Decimal
from db_config import DB_CONFIG
import time

# Vmware path
# /home/user/Django_NextJs_Project/URL_demo/homework
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_ROOT = BASE_DIR / "sample_images"

# 專案 media 目錄（改成你的實際路徑）
# /home/user/Django_NextJs_Project/backend/media/images
BACKEND_ROOT = BASE_DIR.parent
MEDIA_IMAGES = BACKEND_ROOT / "backend"/"media"/"images"



INSERT_BRAND = """
INSERT INTO products_brand (name, parent_brand_id, created_datetime, updated_datetime)
VALUES (%s, NULL, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET updated_datetime = NOW()
RETURNING id;
"""

INSERT_CATEGORY = """
INSERT INTO products_category (name, target_type, parent_category_id, created_datetime, updated_datetime)
VALUES (%s, %s, NULL, NOW(), NOW())
RETURNING id;
"""

INSERT_PRODUCT = """
INSERT INTO products_product (
    name, description, price, original_price,
    stock_quantity, sku, weight, rating,
    is_published, sell_count, brand_id, category_id,
    created_datetime, updated_datetime
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    NOW(), NOW()
)
RETURNING id;
"""

INSERT_IMAGE = """
INSERT INTO products_productimage (
    product_id, image, "isMain", sort_order,
    created_datetime, updated_datetime
) VALUES (
    %s, %s, %s, %s, NOW(), NOW()
);
"""

BRAND_NAMES = [
    "ASUS", "MSI", "Gigabyte", "Intel", "AMD",
    "Corsair", "Samsung", "Kingston", "NVIDIA", "Cooler Master",
]

PRODUCT_NAMES_BY_CATEGORY = {
    "CPU": [
        "Intel Core i5-14400F",
        "Intel Core i7-14700K",
        "AMD Ryzen 5 7600",
        "AMD Ryzen 7 7800X3D",
    ],
    "GPU": [
        "RTX 4060",
        "RTX 4070",
        "RTX 4070 Super",
        "RX 7600",
        "RX 7800 XT",
    ],
    "RAM": [
        "DDR5 16GB 6000MHz",
        "DDR5 32GB 6000MHz",
        "DDR4 16GB 3200MHz",
    ],
    "Motherboard": [
        "B650 Motherboard",
        "Z790 Motherboard",
        "B760 Motherboard",
    ],
    "Storage": [
        "1TB NVMe SSD",
        "2TB NVMe SSD",
        "1TB SATA SSD",
    ],
    "PSU": [
        "650W 80+ Gold PSU",
        "750W 80+ Gold PSU",
        "850W 80+ Gold PSU",
    ],
    "Case": [
        "ATX Mid Tower Case",
        "Full Tower Case",
        "Mini ITX Case",
    ],
    "Cooler": [
        "Air Cooler",
        "240mm AIO Cooler",
        "360mm AIO Cooler",
    ],
}

CATEGORY_DATA = [
    ("CPU", "component"),
    ("GPU", "component"),
    ("RAM", "component"),
    ("Motherboard", "component"),
    ("Storage", "component"),
    ("PSU", "component"),
    ("Case", "component"),
    ("Cooler", "component"),
]

PRODUCT_NAMES = [
    "Intel Core i5-14400F", "Intel Core i7-14700K",
    "AMD Ryzen 5 7600", "AMD Ryzen 7 7800X3D",
    "RTX 4060", "RTX 4070", "RTX 4070 Super", "RX 7600",
    "DDR5 16GB 6000MHz", "DDR5 32GB 6000MHz",
    "B650 Motherboard", "Z790 Motherboard",
    "1TB NVMe SSD", "2TB NVMe SSD",
    "750W 80+ Gold PSU", "850W 80+ Gold PSU",
    "ATX Mid Tower Case", "360mm AIO Cooler",
]


def get_or_create_brands(cur):
    brand_ids = []
    for name in BRAND_NAMES:
        cur.execute(INSERT_BRAND, (name,))
        brand_ids.append(cur.fetchone()[0])
    return brand_ids


def get_or_create_categories(cur):
    result = []
    for name, target_type in CATEGORY_DATA:
        cur.execute(
            "SELECT id FROM products_category WHERE name = %s LIMIT 1;",
            (name,),
        )
        row = cur.fetchone()
        if row:
            result.append((row[0], name))
        else:
            cur.execute(INSERT_CATEGORY, (name, target_type))
            result.append((cur.fetchone()[0], name))
    return result

def pick_image_for_category(category_name: str):
    folder = SAMPLE_ROOT / category_name
    if not folder.is_dir():
        return None
    files = [
        f for f in folder.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    ]
    if not files:
        return None
    return random.choice(files)


def attach_product_image(cur, product_id: int, category_name: str):
    src = pick_image_for_category(category_name)
    if not src:
        return

    MEDIA_IMAGES.mkdir(parents=True, exist_ok=True)

    # 避免重名：加上 product_id
    dest_name = f"{product_id}_{src.name}"
    dest = MEDIA_IMAGES / dest_name
    shutil.copy2(src, dest)

    # DB 存相對路徑（對應 ImageField upload_to='images'）
    db_path = f"images/{dest_name}"

    cur.execute(INSERT_IMAGE, (
        product_id,
        db_path,
        True,   # isMain
        0,      # sort_order
    ))

def gen_products(cur, brand_ids, categories, n=50):
    """
    categories: list of (id, name)
    """
    prefix = int(time.time())

    for i in range(1, n + 1):
        cat_id, cat_name = random.choice(categories)

        # 依 category 選名稱
        name_pool = PRODUCT_NAMES_BY_CATEGORY.get(cat_name)
        if not name_pool:
            name_pool = ["Generic PC Part"]

        base = random.choice(name_pool)
        name = f"{base} #{i}"

        price = Decimal(random.randint(299, 9999)) + Decimal("0.99")
        original = price + Decimal(random.randint(50, 1500))
        sku = f"SKU-GEN-{prefix}-{i}"

        cur.execute(INSERT_PRODUCT, (
            name,
            f"Sample description for {name}",
            price,
            original,
            random.randint(5, 200),
            sku,
            round(random.uniform(0.2, 5.0), 2),
            round(random.uniform(3.5, 5.0), 2),
            True,
            random.randint(0, 500),
            random.choice(brand_ids),
            cat_id,
        ))
        product_id = cur.fetchone()[0]

        # 圖片也依同一個 category
        attach_product_image(cur, product_id, cat_name)

    print(f"Generated {n} products")

def main():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Generating brands...")
        brand_ids = get_or_create_brands(cur)
        print(f"  Brands: {len(brand_ids)}")

        print("Generating categories...")
        category_ids = get_or_create_categories(cur)
        print(f"  Categories: {len(category_ids)}")

        print("Generating products...")
        gen_products(cur, brand_ids, category_ids, n=50)

        conn.commit()
        cur.close()
        print("Done.")
    except Exception as e:
        if conn:
            conn.rollback()
        print("Failed:", e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()