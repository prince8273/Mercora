"""
Fix corrupted product names, categories, and prices across all tenants.

Issues found:
- All names are 'Product <ASIN>' or 'Real Name (WRONG-SKU)' garbage
- All categories are 'General' (should reflect actual product type)
- All HOMESTYLE/FITLIFE/TECHGEAR/VARIOUS prices are flat 29.99 (wrong)
- Some prices are mismatched to product type (e.g. Samsung S24 at $45)
"""
import asyncio, sys
sys.path.insert(0, '.')
from src.database import AsyncSessionLocal
from src.models.product import Product
from sqlalchemy import select

# SKU -> (name, category, realistic_price)
# Price = None means keep existing (it's already reasonable)
SKU_MAP = {
    # ── Home & Kitchen ──────────────────────────────────────────────────
    'HOMESTYLE-0000-MIXY': ('Stainless Steel Mixing Bowl Set 5pc',    'Home & Kitchen',        24.99),
    'HOMESTYLE-0000-OWWW': ('Minimalist Wooden Wall Clock 30cm',      'Home & Kitchen',        34.99),
    'HOMESTYLE-0001-EJII': ('Electric Kettle 1.7L - Rapid Boil',      'Home & Kitchen',        39.99),
    'HOMESTYLE-0001-SEX9': ('Scented Soy Candle Set - 3 Pack',        'Home & Kitchen',        27.99),
    'HOMESTYLE-0002-OLBH': ('Bamboo Cutting Board Large 45x30cm',     'Home & Kitchen',        22.99),
    'HOMESTYLE-0002-SFJB': ('Stainless Steel Water Bottle 1L',        'Home & Kitchen',        28.99),
    'HOMESTYLE-0003-3QZG': ('Non-Stick Frying Pan 28cm',              'Home & Kitchen',        32.99),
    'HOMESTYLE-0004-8FFE': ('Ceramic Coffee Mug Set 4pc',             'Home & Kitchen',        26.99),
    'HOMESTYLE-0004-R6WJ': ('Silicone Kitchen Utensil Set 6pc',       'Home & Kitchen',        19.99),
    'HOMESTYLE-0005-OK5B': ('Vacuum Food Storage Container Set',      'Home & Kitchen',        36.99),
    'HOMESTYLE-0005-I8ZT': ('Stainless Steel Dish Drying Rack',       'Home & Kitchen',        35.99),
    'HOMESTYLE-0008-E8AR': ('Portable Personal Blender 600ml',        'Home & Kitchen',        30.99),
    'COFFEE-MAKER-DELUXE': ('Deluxe Drip Coffee Maker 12-Cup',        'Home & Kitchen',        59.99),
    'KITCHEN-KNIFE-SET':   ('Professional Kitchen Knife Set 6pc',     'Home & Kitchen',        49.99),
    'BED-SHEETS-COTTON':   ('100% Cotton Bed Sheet Set Queen',        'Home & Kitchen',        44.99),
    'PILLOW-MEMORY-FOAM':  ('Ergonomic Memory Foam Pillow',           'Home & Kitchen',        39.99),
    'PLANT-POT-CERAMIC':   ('Ceramic Plant Pot Set 3pc',              'Home & Kitchen',        29.99),
    'MIRROR-BATHROOM':     ('LED Backlit Bathroom Mirror 60cm',       'Home & Kitchen',        79.99),
    'VARIOUS-0003-ATJQ':   ('Multi-Purpose Storage Box Set 3pc',      'Home & Kitchen',        24.99),
    'VARIOUS-0009-6Z4E':   ('Stainless Steel Thermos Flask 500ml',    'Home & Kitchen',        22.99),

    # ── Sports & Fitness ────────────────────────────────────────────────
    'DUMBBELL-SET-20KG':   ('Adjustable Dumbbell Set 20kg',           'Sports & Fitness',      89.99),
    'YOGA-MAT-PREMIUM':    ('Premium Non-Slip Yoga Mat 6mm',          'Sports & Fitness',      34.99),
    'ADIDAS-ULTRABOOST':   ('Adidas Ultraboost 22 Running Shoes',     'Sports & Fitness',     129.99),
    'TENNIS-RACKET-PRO':   ('Professional Tennis Racket 300g',        'Sports & Fitness',      79.99),
    'BICYCLE-MOUNTAIN':    ('Mountain Bicycle 26" 21-Speed',          'Sports & Fitness',     299.99),
    'SPORT-012':           ('Yoga Mat Premium Non-Slip',              'Sports & Fitness',      34.99),
    'FITLIFE-0000-XIZ0':   ('Resistance Band Set - 5 Levels',         'Sports & Fitness',      18.99),
    'FITLIFE-0001-66CE':   ('Foam Roller Deep Tissue Massage',        'Sports & Fitness',      22.99),
    'FITLIFE-0002-230U':   ('Speed Jump Rope - Steel Cable',          'Sports & Fitness',      12.99),
    'FITLIFE-0002-9GPB':   ('Pull-Up Bar Doorframe Mount',            'Sports & Fitness',      29.99),
    'FITLIFE-0003-H8ZX':   ('Anti-Slip Gym Gloves',                   'Sports & Fitness',      14.99),
    'FITLIFE-0003-IOKW':   ('Protein Shaker Bottle 700ml',            'Sports & Fitness',      11.99),
    'FITLIFE-0004-KUKE':   ('Ankle Weights Set 2kg Pair',             'Sports & Fitness',      19.99),
    'FITLIFE-0004-W7FU':   ('Extra Thick Exercise Mat 10mm',          'Sports & Fitness',      27.99),
    'FITLIFE-0005-5TOY':   ('Ab Roller Wheel with Knee Pad',          'Sports & Fitness',      16.99),
    'FITLIFE-0005-NAAU':   ('Cast Iron Kettlebell 16kg',              'Sports & Fitness',      44.99),
    'FITLIFE-0006-5JBE':   ("Men's Compression Shorts",               'Sports & Fitness',      21.99),
    'FITLIFE-0006-65LX':   ('BPA-Free Sports Water Bottle 1L',        'Sports & Fitness',      13.99),
    'FITLIFE-0006-GO74':   ('Padded Palm Workout Gloves',             'Sports & Fitness',      15.99),
    'FITLIFE-0007-58FR':   ('Weighted Skipping Rope',                 'Sports & Fitness',      17.99),
    'FITLIFE-0007-OP1J':   ('Yoga Block Set 2pc - Cork',              'Sports & Fitness',      18.99),
    'FITLIFE-0008-LNGG':   ('Waterproof Gym Bag 40L',                 'Sports & Fitness',      34.99),
    'FITLIFE-0008-Q8NR':   ('Percussion Massage Gun',                 'Sports & Fitness',      59.99),
    'FITLIFE-0008-XAQ3':   ('Balance Board Wobble Trainer',           'Sports & Fitness',      24.99),
    'FITLIFE-0009-2IZ5':   ('Barbell Squat Pad Cushion',              'Sports & Fitness',      12.99),

    # ── Electronics ─────────────────────────────────────────────────────
    'LAMP-LED-DESK':       ('LED Desk Lamp with USB Charging Port',   'Electronics',           45.99),
    'IPHONE-15-PRO':       ('Apple iPhone 15 Pro 256GB',              'Electronics',          999.99),
    'SAMSUNG-S24':         ('Samsung Galaxy S24 128GB',               'Electronics',          799.99),
    'MACBOOK-PRO-M3':      ('Apple MacBook Pro M3 14-inch',           'Electronics',         1599.99),
    'DELL-XPS-13':         ('Dell XPS 13 Laptop Intel i7',            'Electronics',         1099.99),
    'SONY-WH1000XM5':      ('Sony WH-1000XM5 Noise-Canceling Headphones', 'Electronics',     349.99),
    'AIRPODS-PRO-2':       ('Apple AirPods Pro 2nd Generation',       'Electronics',         249.99),
    'NINTENDO-SWITCH':     ('Nintendo Switch OLED 64GB',              'Electronics',         349.99),
    'IPAD-PRO-12':         ('Apple iPad Pro 12.9-inch M2',            'Electronics',         1099.99),
    'VACUUM-ROBOT-V2':     ('Robot Vacuum Cleaner V2 Auto-Mapping',   'Electronics',         299.99),
    'LAPTOP-001':          ('Premium Laptop Pro 15 Intel i9',         'Electronics',         1299.99),
    'CAMERA-006':          ('4K Mirrorless Digital Camera',           'Electronics',         1499.99),
    'PROD-001':            ('Wireless Bluetooth Headphones',          'Electronics',           79.99),
    'VARIOUS-0005-ENXH':   ('Portable Bluetooth Speaker 20W',         'Electronics',           39.99),
    'TECHGEAR-0000-HU01':  ('USB-C Hub 7-in-1 Multiport Adapter',    'Electronics',           34.99),
    'TECHGEAR-0000-N827':  ('Wireless Charging Pad 15W Fast Charge',  'Electronics',           24.99),
    'TECHGEAR-0001-PX31':  ('Adjustable Aluminium Laptop Stand',      'Electronics',           39.99),
    'TECHGEAR-0002-1LMU':  ('Mechanical Keyboard TKL RGB Backlit',    'Electronics',           89.99),
    'TECHGEAR-0005-7XJA':  ('1080p Wide-Angle Webcam',                'Electronics',           49.99),
    'TECHGEAR-0005-D9G7':  ('USB Monitor Light Bar',                  'Electronics',           29.99),
    'TECHGEAR-0006-E7NO':  ('Cable Management Kit 50pc',              'Electronics',           12.99),
    'TECHGEAR-0006-JLYA':  ('Portable SSD 1TB USB 3.2',               'Electronics',           89.99),
    'TECHGEAR-0007-EVFB':  ('Vertical Ergonomic Mouse Wireless',      'Electronics',           44.99),
    'TECHGEAR-0007-G48F':  ('Screen & Lens Cleaning Kit',             'Electronics',            9.99),
    'TECHGEAR-0009-L4AE':  ('Smart Power Strip 6 Outlets + USB',      'Electronics',           34.99),
    'NIKE-AIR-MAX-90':     ('Nike Air Max 90 Sneakers',               'Electronics',          109.99),  # will fix category below

    # ── Clothing ────────────────────────────────────────────────────────
    'DRESS-SUMMER-M':      ("Women's Summer Floral Dress Medium",     'Clothing',              42.99),
    'JACKET-WINTER-XL':    ("Men's Winter Puffer Jacket XL",          'Clothing',              79.99),
    'POLO-SHIRT-CLASSIC':  ('Classic Fit Polo Shirt',                 'Clothing',              29.99),
    'SNEAKERS-WHITE-42':   ('White Canvas Sneakers EU 42',            'Clothing',              44.99),
    'LEVIS-501-JEANS':     ("Levi's 501 Original Fit Jeans",          'Clothing',              69.99),
    'CLOTH-223':           ('Denim Jeans Classic Fit',                'Clothing',              54.99),
    'HOODIE-UNISEX-L':     ('Unisex Pullover Hoodie Large',           'Clothing',              44.99),

    # ── Beauty & Personal Care ───────────────────────────────────────────
    'PERFUME-UNISEX':      ('Unisex Eau de Parfum 100ml',             'Beauty & Personal Care', 89.99),
    'LIPSTICK-RED-MATTE':  ('Matte Red Lipstick Long Lasting',        'Beauty & Personal Care', 18.99),
    'SKINCARE-SERUM-HA':   ('Hyaluronic Acid Serum 30ml',             'Beauty & Personal Care', 32.99),
    'SHAMPOO-ORGANIC':     ('Organic Argan Oil Shampoo 400ml',        'Beauty & Personal Care', 16.99),

    # ── Books ────────────────────────────────────────────────────────────
    'BOOK-MYSTERY-NOVEL':  ('The Silent Patient - Thriller Novel',    'Books',                 14.99),
    'BOOK-COOKING-101':    ('Cooking 101 - Complete Beginner Guide',  'Books',                 19.99),
    'BOOK-HISTORY-WORLD':  ('A Brief History of the World',           'Books',                 16.99),
    'BOOK-PYTHON-GUIDE':   ('Python Programming Complete Guide',      'Books',                 29.99),
    'BOOK-567':            ('Mystery Novel Collection 3-Book Set',    'Books',                 24.99),

    # ── Toys ─────────────────────────────────────────────────────────────
    'TOY-278':             ('Educational Puzzle 1000 Pieces',         'Toys',                  22.99),
}

# Fix Nike category
SKU_MAP['NIKE-AIR-MAX-90'] = ('Nike Air Max 90 Sneakers', 'Clothing', 109.99)


async def fix():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).order_by(Product.tenant_id, Product.sku))
        products = result.scalars().all()

        fixed = skipped = unmapped = 0
        for p in products:
            # Skip the malicious test tenant
            if str(p.tenant_id) == '11111111-1111-1111-1111-111111111111':
                print(f'  SKIP (test tenant): {p.sku}')
                continue

            mapping = SKU_MAP.get(p.sku)
            if not mapping:
                unmapped += 1
                print(f'  UNMAPPED: tenant={str(p.tenant_id)[:8]} sku={p.sku!r}')
                continue

            new_name, new_cat, new_price = mapping
            changed = False

            if p.name != new_name:
                p.name = new_name
                changed = True
            if p.category != new_cat:
                p.category = new_cat
                changed = True
            if new_price and abs(float(p.price) - new_price) > 0.01:
                p.price = new_price
                changed = True

            if changed:
                fixed += 1
                print(f'  FIXED [{str(p.tenant_id)[:8]}] {p.sku!r:35} -> {new_name!r} [{new_cat}] £{new_price}')
            else:
                skipped += 1

        await db.commit()
        print(f'\nDone. Fixed={fixed}  Already OK={skipped}  Unmapped={unmapped}')

asyncio.run(fix())
