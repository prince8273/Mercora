#!/usr/bin/env python3
"""
Test Data Population Script

This script populates the backend with test data by:
1. Authenticating with the API
2. Uploading test_products.csv
3. Fetching real product UUIDs from the database
4. Generating test_reviews.csv with real UUIDs
5. Generating test_sales.csv with real UUIDs
6. Uploading the generated CSVs

Usage:
    python populate_test_data.py
"""

import requests
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "demo@example.com"
PASSWORD = "demo123"

# Review templates for realistic text generation
POSITIVE_REVIEWS = [
    "Absolutely love this product! {feature} is amazing and {benefit}. Best purchase this year.",
    "Excellent quality! {feature} exceeded my expectations. Highly recommend.",
    "Perfect {product_type}! {feature} works flawlessly and {benefit}.",
    "Outstanding product! {feature} is top-notch. Will definitely buy again.",
    "Great value for money! {feature} is impressive and {benefit}.",
    "Couldn't be happier! {feature} is exactly what I needed.",
    "Fantastic purchase! {feature} is brilliant and {benefit}.",
    "Highly satisfied! {feature} performs excellently.",
]

NEUTRAL_REVIEWS = [
    "Good {product_type} overall. {feature} works well but {issue}.",
    "Decent product. {feature} is fine but could be improved.",
    "It's okay. {feature} meets expectations but {issue}.",
    "Average quality. {feature} works as described but {issue}.",
    "Not bad. {feature} is acceptable though {issue}.",
]

NEGATIVE_REVIEWS = [
    "Disappointed. {feature} {issue} and doesn't meet expectations.",
    "Poor quality. {feature} {issue}. Would not recommend.",
    "Not satisfied. {feature} {issue}. Expected better.",
    "Below average. {feature} {issue}. Returning this.",
    "Waste of money. {feature} {issue}. Very frustrating.",
]

# Feature and benefit templates
FEATURES = {
    "Electronics": ["Sound quality", "Battery life", "Build quality", "Display", "Performance", "Connectivity"],
    "Clothing": ["Fit", "Fabric quality", "Design", "Comfort", "Durability", "Style"],
    "Home & Garden": ["Design", "Quality", "Functionality", "Durability", "Ease of use", "Appearance"],
    "Sports": ["Quality", "Durability", "Performance", "Comfort", "Design", "Value"],
    "Books": ["Content", "Writing style", "Information", "Examples", "Organization", "Depth"],
    "Toys": ["Quality", "Fun factor", "Durability", "Design", "Value", "Entertainment"],
}

BENEFITS = [
    "lasts all day",
    "works perfectly",
    "exceeded expectations",
    "great for daily use",
    "very reliable",
    "easy to use",
    "looks amazing",
    "feels premium",
]

ISSUES = [
    "could be more comfortable",
    "the price is a bit high",
    "delivery took longer than expected",
    "instructions could be clearer",
    "packaging was damaged",
    "color slightly different than pictured",
]


class TestDataPopulator:
    """Handles test data population"""
    
    def __init__(self):
        self.token = None
        self.products = []
        
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        print("🔐 Authenticating...")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={
                    "username": EMAIL,
                    "password": PASSWORD
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            print(f"✅ Authentication successful")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def upload_products(self) -> bool:
        """Upload test_products.csv"""
        print("\n📦 Uploading products...")
        try:
            with open("test_products.csv", "rb") as f:
                files = {"file": ("test_products.csv", f, "text/csv")}
                response = requests.post(
                    f"{BASE_URL}/csv/upload/products",
                    files=files,
                    headers=self.get_headers()
                )
                response.raise_for_status()
                data = response.json()
                count = data.get("products_uploaded", 0)
                print(f"✅ Uploaded {count} products")
                return True
        except FileNotFoundError:
            print("❌ test_products.csv not found")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Product upload failed: {e}")
            return False
    
    def fetch_products(self) -> bool:
        """Fetch all products to get real UUIDs"""
        print("\n🔍 Fetching product UUIDs...")
        try:
            response = requests.get(
                f"{BASE_URL}/products",
                headers=self.get_headers()
            )
            response.raise_for_status()
            self.products = response.json()
            print(f"✅ Fetched {len(self.products)} products")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch products: {e}")
            return False
    
    def generate_review_text(self, rating: int, category: str, product_name: str) -> str:
        """Generate realistic review text based on rating"""
        # Select template based on rating
        if rating >= 4:
            template = random.choice(POSITIVE_REVIEWS)
        elif rating == 3:
            template = random.choice(NEUTRAL_REVIEWS)
        else:
            template = random.choice(NEGATIVE_REVIEWS)
        
        # Get features for category
        features = FEATURES.get(category, FEATURES["Electronics"])
        feature = random.choice(features)
        
        # Determine product type
        product_type = "product"
        if "shirt" in product_name.lower() or "shoes" in product_name.lower():
            product_type = "item"
        elif "book" in product_name.lower():
            product_type = "book"
        elif "toy" in product_name.lower():
            product_type = "toy"
        
        # Fill in template
        text = template.format(
            feature=feature,
            benefit=random.choice(BENEFITS),
            issue=random.choice(ISSUES),
            product_type=product_type
        )
        
        return text
    
    def generate_reviews(self, count: int = 30) -> bool:
        """Generate test_reviews.csv with real product UUIDs"""
        print(f"\n📝 Generating {count} reviews...")
        
        if not self.products:
            print("❌ No products available")
            return False
        
        reviews = []
        marketplaces = ["Amazon", "Walmart", "eBay", "Etsy", "Direct"]
        
        for i in range(count):
            product = random.choice(self.products)
            product_id = product["id"]
            category = product.get("category", "General")
            name = product.get("name", "Product")
            
            # Generate rating with realistic distribution (more 4-5 stars)
            rating = random.choices(
                [1, 2, 3, 4, 5],
                weights=[5, 10, 15, 35, 35]  # Skewed towards positive
            )[0]
            
            # Generate review text
            text = self.generate_review_text(rating, category, name)
            
            # Select source (prefer product's marketplace)
            source = product.get("marketplace", random.choice(marketplaces))
            
            reviews.append({
                "product_id": product_id,
                "rating": rating,
                "text": text,
                "source": source
            })
        
        # Write to CSV
        try:
            with open("test_reviews.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["product_id", "rating", "text", "source"])
                writer.writeheader()
                writer.writerows(reviews)
            print(f"✅ Generated test_reviews.csv with {count} reviews")
            return True
        except Exception as e:
            print(f"❌ Failed to generate reviews: {e}")
            return False
    
    def generate_sales(self, count: int = 25, days: int = 30) -> bool:
        """Generate test_sales.csv with real product UUIDs for last N days"""
        print(f"\n💰 Generating {count} sales records for last {days} days...")
        
        if not self.products:
            print("❌ No products available")
            return False
        
        sales = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for i in range(count):
            product = random.choice(self.products)
            product_id = product["id"]
            price = float(product.get("price", 10.0))
            marketplace = product.get("marketplace", "Amazon")
            
            # Generate random quantity (weighted towards smaller orders)
            quantity = random.choices(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                weights=[30, 25, 15, 10, 8, 5, 3, 2, 1, 1]
            )[0]
            
            # Calculate revenue
            revenue = round(quantity * price, 2)
            
            # Generate random date within range
            days_diff = (end_date - start_date).days
            random_days = random.randint(0, days_diff)
            sale_date = start_date + timedelta(days=random_days)
            date_str = sale_date.strftime("%Y-%m-%d")
            
            sales.append({
                "product_id": product_id,
                "quantity": quantity,
                "revenue": revenue,
                "date": date_str,
                "marketplace": marketplace
            })
        
        # Sort by date
        sales.sort(key=lambda x: x["date"])
        
        # Write to CSV
        try:
            with open("test_sales.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["product_id", "quantity", "revenue", "date", "marketplace"])
                writer.writeheader()
                writer.writerows(sales)
            print(f"✅ Generated test_sales.csv with {count} sales records")
            return True
        except Exception as e:
            print(f"❌ Failed to generate sales: {e}")
            return False
    
    def upload_reviews(self) -> bool:
        """Upload test_reviews.csv"""
        print("\n📤 Uploading reviews...")
        try:
            with open("test_reviews.csv", "rb") as f:
                files = {"file": ("test_reviews.csv", f, "text/csv")}
                response = requests.post(
                    f"{BASE_URL}/csv/upload/reviews",
                    files=files,
                    headers=self.get_headers()
                )
                response.raise_for_status()
                data = response.json()
                count = data.get("reviews_uploaded", 0)
                avg_rating = data.get("analysis", {}).get("average_rating", 0)
                print(f"✅ Uploaded {count} reviews (avg rating: {avg_rating:.2f})")
                return True
        except FileNotFoundError:
            print("❌ test_reviews.csv not found")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Review upload failed: {e}")
            return False
    
    def upload_sales(self) -> bool:
        """Upload test_sales.csv"""
        print("\n📤 Uploading sales...")
        try:
            with open("test_sales.csv", "rb") as f:
                files = {"file": ("test_sales.csv", f, "text/csv")}
                response = requests.post(
                    f"{BASE_URL}/csv/upload/sales",
                    files=files,
                    headers=self.get_headers()
                )
                response.raise_for_status()
                data = response.json()
                count = data.get("sales_records_uploaded", 0)
                total_revenue = data.get("analysis", {}).get("total_revenue", 0)
                total_quantity = data.get("analysis", {}).get("total_quantity", 0)
                print(f"✅ Uploaded {count} sales records")
                print(f"   Total revenue: ${total_revenue:,.2f}")
                print(f"   Total units sold: {total_quantity:,}")
                return True
        except FileNotFoundError:
            print("❌ test_sales.csv not found")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Sales upload failed: {e}")
            return False
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*60)
        print("📊 DATA POPULATION SUMMARY")
        print("="*60)
        print(f"✅ Products: {len(self.products)} uploaded")
        
        # Count reviews
        try:
            with open("test_reviews.csv", "r") as f:
                review_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"✅ Reviews: {review_count} generated and uploaded")
        except:
            print("❌ Reviews: Failed")
        
        # Count sales
        try:
            with open("test_sales.csv", "r") as f:
                sales_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"✅ Sales: {sales_count} generated and uploaded")
        except:
            print("❌ Sales: Failed")
        
        print("="*60)
        print("🎉 Dashboard is now fully populated with test data!")
        print("="*60)
    
    def run(self):
        """Run the complete data population process"""
        print("="*60)
        print("🚀 TEST DATA POPULATION SCRIPT")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ Failed to authenticate. Exiting.")
            sys.exit(1)
        
        # Step 2: Upload products
        if not self.upload_products():
            print("\n❌ Failed to upload products. Exiting.")
            sys.exit(1)
        
        # Step 3: Fetch products to get UUIDs
        if not self.fetch_products():
            print("\n❌ Failed to fetch products. Exiting.")
            sys.exit(1)
        
        # Step 4: Generate reviews
        if not self.generate_reviews(count=30):
            print("\n❌ Failed to generate reviews. Exiting.")
            sys.exit(1)
        
        # Step 5: Generate sales
        if not self.generate_sales(count=25, days=30):
            print("\n❌ Failed to generate sales. Exiting.")
            sys.exit(1)
        
        # Step 6: Upload reviews
        if not self.upload_reviews():
            print("\n❌ Failed to upload reviews. Exiting.")
            sys.exit(1)
        
        # Step 7: Upload sales
        if not self.upload_sales():
            print("\n❌ Failed to upload sales. Exiting.")
            sys.exit(1)
        
        # Print summary
        self.print_summary()


if __name__ == "__main__":
    populator = TestDataPopulator()
    populator.run()
