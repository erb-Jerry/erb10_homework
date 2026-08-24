# generate_template.py
import argparse
import csv
from pathlib import Path

# Headers matching database schema
HEADERS = [
    "id",
    "name",
    "description",
    "price",
    "original_price",
    "stock_quantity",
    "sku",
    "weight",
    "rating",
    "is_published",
    "sell_count",
    "brand_id",
    "category_id",
    "created_datetime",
    "updated_datetime",
]

# Sample placeholder row for guidance
SAMPLE_ROW = [
    "",  # id (leave empty for new items, or supply ID for update)
    "Sample Product Name",
    "Sample description text here",
    "99.99",  # price
    "120.00",  # original_price
    "100",  # stock_quantity
    "SKU-12345",  # sku
    "0.5",  # weight
    "4.5",  # rating
    "True",  # is_published
    "0",  # sell_count
    "1",  # brand_id
    "1",  # category_id
    "2026-08-25 12:00:00",  # created_datetime
    "2026-08-25 12:00:00",  # updated_datetime
]


def create_template(filename="products_import_template.csv", include_sample=True):
    # Target current working directory
    target = Path.cwd() / filename

    with open(target, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

        if include_sample:
            writer.writerow(SAMPLE_ROW)

    print(f"Template successfully generated -> {target.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a CSV import template in the current directory."
    )
    parser.add_argument(
        "--filename",
        "-f",
        type=str,
        default="products_import_template.csv",
        help="Filename for the template",
    )
    parser.add_argument(
        "--no-sample",
        action="store_true",
        help="Generate headers only (omit sample row)",
    )

    args = parser.parse_args()
    create_template(filename=args.filename, include_sample=not args.no_sample)