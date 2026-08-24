## Getting Started

db_config.py
* postgreSQL config

gen_data.py
```
BACKEND_ROOT = "Your Backend Root path"
```
```
MEDIA_IMAGES = "BACKEND_ROOT / MEDIA_URL / IMAGES FOLDER"
```

### Commands

```
python gen_data.py
```
* gen the products, profile_image base on categroy name, name base on category sub list name

```
python generate_template.py
```
* gen the template with header and 1 row example for import example.

```
python export_products.py
```
* export all product rows into csv file

```
python import_products.py [products_import_template.csv]
```
* import csv file into products table

