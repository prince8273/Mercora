"""Transform Amazon product dataset to system-compatible format"""
import pandas as pd
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_prices(prices_str):
    """Parse prices JSON string and extract latest price"""
    try:
        if pd.isna(prices_str) or not prices_str:
            return None, None
        
        prices = json.loads(prices_str)
        if not prices:
            return None, None
        
        # Get most recent price
        latest = max(prices, key=lambda x: x.get('dateAdded', ''))
        return latest.get('amountMax'), latest.get('currency', 'USD')
    except:
        return None, None


def transform_to_products(df):
    """Transform Amazon data to products CSV format"""
    products = []
    
    for idx, row in df.iterrows():
        # Parse prices
        price, currency = parse_prices(row.get('prices'))
        
        # Extract basic product info
        product = {
            'sku': row.get('asins', f'ASIN-{idx}'),
            'name': row.get('name', 'Unknown Product'),
            'category': row.get('categories', '').split(',')[0] if pd.notna(row.get('categories')) else 'General',
            'price': price if price else 99.99,
            'currency': currency if currency else 'USD',
            'marketplace': 'Amazon',
            'inventory_level': 100,  # Default since not in source data
            'brand': row.get('brand', ''),
            'manufacturer': row.get('manufacturer', ''),
            'weight': row.get('weight', ''),
            'dimension': row.get('dimension', ''),
        }
        
        products.append(product)
    
    return pd.DataFrame(products)


def transform_to_reviews(df):
    """Transform Amazon data to reviews CSV format"""
    reviews = []
    
    for idx, row in df.iterrows():
        sku = row.get('asins', f'ASIN-{idx}')
        
        # Extract review fields
        review_date = row.get('reviews.date')
        review_rating = row.get('reviews.rating')
        review_text = row.get('reviews.text')
        review_title = row.get('reviews.title')
        review_username = row.get('reviews.username')
        review_helpful = row.get('reviews.numHelpful')
        
        # Only add if we have review data
        if pd.notna(review_text) and pd.notna(review_rating):
            review = {
                'product_sku': sku,
                'rating': int(review_rating) if pd.notna(review_rating) else 5,
                'review_text': str(review_text)[:500] if pd.notna(review_text) else '',  # Limit length
                'review_title': str(review_title) if pd.notna(review_title) else '',
                'reviewer_name': str(review_username) if pd.notna(review_username) else 'Anonymous',
                'review_date': review_date if pd.notna(review_date) else datetime.now().strftime('%Y-%m-%d'),
                'num_helpful': int(review_helpful) if pd.notna(review_helpful) else 0,
                'user_city': row.get('reviews.userCity', ''),
                'user_province': row.get('reviews.userProvince', ''),
            }
            
            reviews.append(review)
    
    return pd.DataFrame(reviews)


def main():
    """Main transformation function"""
    if len(sys.argv) < 2:
        print("Usage: python transform_amazon_data.py <input_csv_file>")
        print("\nThis script transforms Amazon product data to system-compatible format")
        print("It will create two files:")
        print("  - products_transformed.csv")
        print("  - reviews_transformed.csv")
        return
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"❌ Error: File not found: {input_file}")
        return
    
    print(f"📂 Reading Amazon data from: {input_file}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} rows")
        
        # Show columns
        print(f"\n📋 Columns found: {len(df.columns)}")
        print(f"   Sample columns: {', '.join(df.columns[:5].tolist())}...")
        
        # Transform to products
        print("\n🔄 Transforming to products format...")
        products_df = transform_to_products(df)
        
        # Save products
        products_file = 'products_transformed.csv'
        products_df.to_csv(products_file, index=False)
        print(f"✅ Created: {products_file} ({len(products_df)} products)")
        
        # Transform to reviews
        print("\n🔄 Transforming to reviews format...")
        reviews_df = transform_to_reviews(df)
        
        if len(reviews_df) > 0:
            # Save reviews
            reviews_file = 'reviews_transformed.csv'
            reviews_df.to_csv(reviews_file, index=False)
            print(f"✅ Created: {reviews_file} ({len(reviews_df)} reviews)")
        else:
            print("⚠️  No reviews found in dataset")
        
        # Show sample data
        print("\n" + "="*60)
        print("TRANSFORMATION COMPLETE!")
        print("="*60)
        
        print("\n📊 Products Sample:")
        print(products_df.head(3).to_string())
        
        if len(reviews_df) > 0:
            print("\n📊 Reviews Sample:")
            print(reviews_df.head(3).to_string())
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print(f"1. Upload products: python upload_csv.py {products_file} products")
        if len(reviews_df) > 0:
            print(f"2. Upload reviews: python upload_csv.py {reviews_file} reviews")
        print("3. Or use the UI: http://localhost:3000/upload")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error transforming data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
