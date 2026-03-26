"""
Seed Indian-style mixed reviews for existing HomeStyle products
"""
import sqlite3
import uuid
import random
from datetime import datetime, timedelta

TENANT_ID = '9b00dc26-cec5-4eeb-ba9e-cf6b65cdaeb6'
conn = sqlite3.connect('ecommerce_intelligence.db')
cur = conn.cursor()

# Check exact columns
cur.execute("PRAGMA table_info(reviews)")
cols = [c[1] for c in cur.fetchall()]
print("Review columns:", cols)

cur.execute("SELECT id, name FROM products WHERE tenant_id = ?", (TENANT_ID,))
products = cur.fetchall()
print(f"Products found: {len(products)}")
conn.close()
