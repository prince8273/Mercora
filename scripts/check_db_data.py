"""Check database data for TechGear Pro tenant"""
import sqlite3

# Connect to database
conn = sqlite3.connect('ecommerce_intelligence.db')
cursor = conn.cursor()

# TechGear Pro tenant ID
tenant_id = '54d459ab-4ae8-480a-9d1c-d53b218a4fb2'

# Check products
cursor.execute('SELECT COUNT(*) FROM products WHERE tenant_id=?', (tenant_id,))
product_count = cursor.fetchone()[0]
print(f"✓ Products for TechGear Pro: {product_count}")

# Check sales records
cursor.execute('SELECT COUNT(*) FROM sales_records WHERE tenant_id=?', (tenant_id,))
sales_count = cursor.fetchone()[0]
print(f"✓ Sales records for TechGear Pro: {sales_count}")

# Check total revenue
cursor.execute('SELECT SUM(revenue) FROM sales_records WHERE tenant_id=?', (tenant_id,))
total_revenue = cursor.fetchone()[0]
print(f"✓ Total revenue for TechGear Pro: ${total_revenue:.2f}" if total_revenue else "✓ Total revenue: $0.00")

# Check date range
cursor.execute('SELECT MIN(date), MAX(date) FROM sales_records WHERE tenant_id=?', (tenant_id,))
min_date, max_date = cursor.fetchone()
print(f"✓ Sales date range: {min_date} to {max_date}")

# Check sample products
cursor.execute('SELECT name, price, inventory_level FROM products WHERE tenant_id=? LIMIT 5', (tenant_id,))
print("\n✓ Sample products:")
for name, price, inventory in cursor.fetchall():
    print(f"  - {name}: ${price} (Stock: {inventory})")

conn.close()
print("\n✅ Database is running and has data!")
