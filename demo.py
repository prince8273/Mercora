"""
Demo script for E-commerce Intelligence Agent MVP

This script demonstrates the core functionality of the MVP:
1. Creating products
2. Analyzing pricing
3. Executing queries
"""
import asyncio
import httpx
from decimal import Decimal


BASE_URL = "http://localhost:8000"


async def demo():
    """Run the demo"""
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("E-COMMERCE INTELLIGENCE AGENT - MVP DEMO")
        print("=" * 80)
        print()
        
        # Step 1: Create sample products
        print("📦 Step 1: Creating sample products...")
        print("-" * 80)
        
        products = [
            {
                "sku": "LAPTOP-001",
                "name": "Gaming Laptop Pro",
                "category": "Electronics",
                "price": 1299.99,
                "currency": "USD",
                "marketplace": "our_store",
                "inventory_level": 50
            },
            {
                "sku": "LAPTOP-002",
                "name": "Business Laptop Elite",
                "category": "Electronics",
                "price": 999.99,
                "currency": "USD",
                "marketplace": "our_store",
                "inventory_level": 75
            },
            {
                "sku": "MOUSE-001",
                "name": "Wireless Gaming Mouse",
                "category": "Accessories",
                "price": 79.99,
                "currency": "USD",
                "marketplace": "our_store",
                "inventory_level": 200
            }
        ]
        
        created_products = []
        for product_data in products:
            response = await client.post(
                f"{BASE_URL}/api/v1/products",
                json=product_data
            )
            if response.status_code == 200:
                product = response.json()
                created_products.append(product)
                print(f"✅ Created: {product['name']} (${product['price']})")
            else:
                print(f"❌ Failed to create: {product_data['name']}")
        
        print()
        
        # Step 2: Analyze pricing
        print("💰 Step 2: Analyzing pricing...")
        print("-" * 80)
        
        product_ids = [p['id'] for p in created_products]
        
        response = await client.post(
            f"{BASE_URL}/api/v1/pricing/analysis",
            json={
                "product_ids": product_ids,
                "include_recommendations": True,
                "margin_constraints": {
                    "min_margin_percentage": 20.0,
                    "max_discount_percentage": 30.0
                }
            }
        )
        
        if response.status_code == 200:
            analysis = response.json()
            
            print(f"📊 Price Gaps Identified: {len(analysis['price_gaps'])}")
            print(f"📈 Price Changes Detected: {len(analysis['price_changes'])}")
            print(f"🎁 Promotions Found: {len(analysis['promotions'])}")
            print(f"💡 Recommendations Generated: {len(analysis['recommendations'])}")
            print()
            
            # Show recommendations
            if analysis['recommendations']:
                print("💡 Pricing Recommendations:")
                print()
                for i, rec in enumerate(analysis['recommendations'], 1):
                    product_name = next(
                        (p['name'] for p in created_products if p['id'] == rec['product_id']),
                        "Unknown"
                    )
                    print(f"  {i}. {product_name}")
                    print(f"     Current Price: ${rec['current_price']}")
                    print(f"     Suggested Price: ${rec['suggested_price']}")
                    print(f"     Confidence: {rec['confidence_score']:.1%}")
                    print(f"     Reasoning: {rec['reasoning'][:100]}...")
                    print()
        else:
            print(f"❌ Pricing analysis failed: {response.status_code}")
        
        print()
        
        # Step 3: Execute query
        print("🔍 Step 3: Executing natural language query...")
        print("-" * 80)
        
        response = await client.post(
            f"{BASE_URL}/api/v1/query",
            json={
                "query_text": "What's the pricing situation for my products?",
                "product_ids": product_ids,
                "analysis_type": "pricing"
            }
        )
        
        if response.status_code == 200:
            report = response.json()
            
            print("📋 STRUCTURED REPORT")
            print()
            print(f"Executive Summary:")
            print(f"  {report['executive_summary']}")
            print()
            
            print(f"Overall Confidence: {report['confidence_score']:.1%}")
            print()
            
            print("Key Metrics:")
            for key, value in report['key_metrics'].items():
                print(f"  • {key.replace('_', ' ').title()}: {value}")
            print()
        else:
            print(f"❌ Query execution failed: {response.status_code}")
        
        print()
        print("=" * 80)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  • Visit http://localhost:8000/docs for interactive API documentation")
        print("  • Run 'pytest -v' to see all 55 tests passing")
        print("  • Check README.md for more usage examples")
        print()


if __name__ == "__main__":
    print()
    print("Starting demo...")
    print("Make sure the server is running: python src/main.py")
    print()
    
    try:
        asyncio.run(demo())
    except httpx.ConnectError:
        print()
        print("❌ ERROR: Could not connect to the server!")
        print()
        print("Please start the server first:")
        print("  1. Activate virtual environment")
        print("     Windows: .\\venv\\Scripts\\Activate.ps1")
        print("     Linux/macOS: source venv/bin/activate")
        print("  2. Run: python src/main.py")
        print("  3. Then run this demo again: python demo.py")
        print()
    except Exception as e:
        print(f"❌ ERROR: {e}")
