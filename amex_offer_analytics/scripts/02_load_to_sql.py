"""
02_load_to_sql.py
Loads the CSVs in ./data into a local SQLite database (amex_offers.db)
so you can run real SQL against it — no server install needed.

"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE_DIR, "amex_offers.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)

tables = {
    "customers": "customers.csv",
    "merchants": "merchants.csv",
    "offers": "offers.csv",
    "offer_exposures": "offer_exposures.csv",
}

for table, filename in tables.items():
    df = pd.read_csv(os.path.join(DATA_DIR, filename))
    df.to_sql(table, conn, if_exists="replace", index=False)
    print(f"Loaded {table:<20} {len(df):>7,} rows")

cur = conn.cursor()
cur.execute("CREATE INDEX IF NOT EXISTS idx_exp_customer ON offer_exposures(customer_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_exp_offer ON offer_exposures(offer_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_exp_category ON offer_exposures(category)")
conn.commit()
conn.close()

print(f"\nDatabase ready at {DB_PATH}")
print("Open it with 'DB Browser for SQLite' (GUI) or query it from Python — see 03_sql_analysis.py")
