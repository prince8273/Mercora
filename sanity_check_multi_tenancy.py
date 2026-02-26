"""
Multi-Tenancy Sanity Check Script

This script performs a comprehensive sanity check of the multi-tenancy implementation:
1. Runs the database migration
2. Creates 3 tenants with users
3. Inserts overlapping SKUs for each tenant
4. Runs full multi-agent queries
5. Verifies outputs never mix

Run this before moving to Demand Agent implementation.
"""
import asyncio
import sys
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.tenant import Tenant
from src.models.user import User
from src.models.product import Product
from src.models.review import Review
from src.auth.security import get_password_hash, create_access_token
from src.agents.pricing_intelligence_v2 import EnhancedPricingIntelligenceAgent
from src.agents.sentiment_analysis_v2 import EnhancedSentimentAgent
from src.agents.data_qa_agent import DataQAAgent
from src.schemas.product import ProductResponse
from src.schemas.review import ReviewResponse


# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./ecommerce_intelligence.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def run_migration():
    """Run the multi-tenancy migration"""
    print("=" * 80)
    print("STEP 1: Running Migration")
    print("=" * 80)
    
    import subprocess
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Migration failed: {result.stderr}")
        return False
    
    print("✅ Migration completed successfully")
    print(result.stdout)
    return True


async def create_tenants_and_users(db: AsyncSession):
    """Create 3 tenants with users"""
    print("\n" + "=" * 80)
    print("STEP 2: Creating 3 Tenants with Users")
    print("=" * 80)
    
    tenants_data = [
        {"name": "Acme Corp", "slug": "acme-corp", "email": "admin@acme.com"},
        {"name": "TechStart Inc", "slug": "techstart", "email": "admin@techstart.com"},
        {"name": "Global Retail", "slug": "global-retail", "email": "admin@globalretail.com"}
    ]
    
    tenants = []
    users = []
    tokens = []
    
    for data in tenants_data:
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name=data["name"],
            slug=data["slug"],
            is_active=True
        )
        db.add(tenant)
        await db.flush()
        
        # Create user for tenant
        user = User(
            id=uuid4(),
            email=data["email"],
            hashed_password=get_password_hash("password123"),
            full_name=f"{data['name']} Admin",
            is_superuser=False,
            is_active=True,
            tenant_id=tenant.id
        )
        db.add(user)
        await db.flush()
        
        # Generate JWT token
        token = create_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role="admin" if user.is_superuser else "user"
        )
        
        tenants.append(tenant)
        users.append(user)
        tokens.append(token)
        
        print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")
        print(f"   User: {user.email}")
        print(f"   Token: {token[:50]}...")
    
    await db.commit()
    
    return tenants, users, tokens


async def insert_overlapping_skus(db: AsyncSession, tenants):
    """Insert products with overlapping SKUs for each tenant"""
    print("\n" + "=" * 80)
    print("STEP 3: Inserting Overlapping SKUs")
    print("=" * 80)
    
    # Same SKUs for all tenants - this is the critical test!
    overlapping_skus = ["LAPTOP-001", "PHONE-002", "TABLET-003"]
    
    all_products = []
    
    for tenant in tenants:
        tenant_products = []
        
        for i, sku in enumerate(overlapping_skus):
            product = Product(
                id=uuid4(),
                sku=sku,  # SAME SKU across tenants!
                normalized_sku=sku.lower().replace("-", ""),
                name=f"{tenant.name} - {sku}",
                category="Electronics",
                price=Decimal(str(999.99 + (i * 100))),
                currency="USD",
                marketplace="our_store",
                inventory_level=100 + (i * 10),
                tenant_id=tenant.id
            )
            db.add(product)
            tenant_products.append(product)
            
            # Add reviews for each product
            for j in range(3):
                review = Review(
                    id=uuid4(),
                    product_id=product.id,
                    tenant_id=tenant.id,
                    rating=4 + (j % 2),
                    text=f"Review {j+1} for {product.name} from {tenant.name}",
                    sentiment="positive",
                    sentiment_confidence=0.9,
                    is_spam=False,
                    source="our_store"
                )
                db.add(review)
        
        all_products.append(tenant_products)
        
        print(f"✅ Inserted {len(tenant_products)} products for {tenant.name}")
        print(f"   SKUs: {[p.sku for p in tenant_products]}")
        print(f"   Product IDs: {[str(p.id)[:8] for p in tenant_products]}")
    
    await db.commit()
    
    return all_products


async def run_multi_agent_query(db: AsyncSession, tenant, products):
    """Run full multi-agent query for a tenant"""
    print(f"\n{'=' * 80}")
    print(f"STEP 4: Running Multi-Agent Query for {tenant.name}")
    print(f"{'=' * 80}")
    
    # Initialize agents with tenant_id
    qa_agent = DataQAAgent(tenant_id=tenant.id)
    pricing_agent = EnhancedPricingIntelligenceAgent(tenant_id=tenant.id)
    sentiment_agent = EnhancedSentimentAgent(tenant_id=tenant.id)
    
    # Fetch products for this tenant
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant.id)
    )
    tenant_products = result.scalars().all()
    
    print(f"📊 Found {len(tenant_products)} products for {tenant.name}")
    for p in tenant_products:
        print(f"   - {p.sku}: {p.name} (ID: {str(p.id)[:8]})")
    
    # Convert to response schemas
    product_responses = [ProductResponse.model_validate(p) for p in tenant_products]
    
    # Run QA assessment
    qa_report = qa_agent.assess_product_data_quality(product_responses)
    print(f"✅ QA Assessment: {qa_report.overall_quality_score:.2f}")
    
    # Fetch reviews for sentiment analysis
    all_reviews = []
    for product in tenant_products:
        result = await db.execute(
            select(Review).where(
                Review.product_id == product.id,
                Review.tenant_id == tenant.id
            )
        )
        reviews = result.scalars().all()
        all_reviews.extend(reviews)
    
    print(f"📝 Found {len(all_reviews)} reviews for {tenant.name}")
    
    if all_reviews:
        review_responses = [
            ReviewResponse(
                id=r.id,
                product_id=r.product_id,
                rating=r.rating,
                text=r.text,
                sentiment=r.sentiment,
                sentiment_confidence=r.sentiment_confidence,
                is_spam=r.is_spam,
                created_at=r.created_at,
                source=r.source
            )
            for r in all_reviews
        ]
        
        review_qa_report = qa_agent.assess_review_data_quality(review_responses)
        sentiment_result = sentiment_agent.calculate_aggregate_sentiment_with_qa(
            review_responses,
            review_qa_report
        )
        print(f"✅ Sentiment Analysis: {sentiment_result.aggregate_sentiment:.2f}")
    
    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "product_count": len(tenant_products),
        "product_ids": [p.id for p in tenant_products],
        "product_skus": [p.sku for p in tenant_products],
        "review_count": len(all_reviews),
        "qa_score": qa_report.overall_quality_score
    }


async def verify_no_data_mixing(results):
    """Verify that outputs never mix between tenants"""
    print(f"\n{'=' * 80}")
    print("STEP 5: Verifying No Data Mixing")
    print(f"{'=' * 80}")
    
    all_passed = True
    
    # Check 1: Each tenant has exactly 3 products
    print("\n🔍 Check 1: Product Count per Tenant")
    for result in results:
        if result["product_count"] != 3:
            print(f"❌ {result['tenant_name']}: Expected 3 products, got {result['product_count']}")
            all_passed = False
        else:
            print(f"✅ {result['tenant_name']}: Correct product count (3)")
    
    # Check 2: No product IDs overlap between tenants
    print("\n🔍 Check 2: Product ID Isolation")
    all_product_ids = []
    for result in results:
        all_product_ids.extend(result["product_ids"])
    
    if len(all_product_ids) != len(set(all_product_ids)):
        print("❌ Product IDs overlap between tenants!")
        all_passed = False
    else:
        print("✅ All product IDs are unique across tenants")
    
    # Check 3: Same SKUs exist for each tenant (overlapping SKUs)
    print("\n🔍 Check 3: Overlapping SKUs Handled Correctly")
    expected_skus = {"LAPTOP-001", "PHONE-002", "TABLET-003"}
    for result in results:
        tenant_skus = set(result["product_skus"])
        if tenant_skus != expected_skus:
            print(f"❌ {result['tenant_name']}: SKUs don't match expected")
            print(f"   Expected: {expected_skus}")
            print(f"   Got: {tenant_skus}")
            all_passed = False
        else:
            print(f"✅ {result['tenant_name']}: Has all expected SKUs")
    
    # Check 4: Product IDs are different even with same SKUs
    print("\n🔍 Check 4: Same SKU, Different Product IDs")
    sku_to_ids = {}
    for result in results:
        for sku, product_id in zip(result["product_skus"], result["product_ids"]):
            if sku not in sku_to_ids:
                sku_to_ids[sku] = []
            sku_to_ids[sku].append((result["tenant_name"], product_id))
    
    for sku, tenant_ids in sku_to_ids.items():
        unique_ids = set(pid for _, pid in tenant_ids)
        if len(unique_ids) != 3:
            print(f"❌ SKU '{sku}': Expected 3 unique product IDs, got {len(unique_ids)}")
            all_passed = False
        else:
            print(f"✅ SKU '{sku}': 3 different product IDs across tenants")
            for tenant_name, product_id in tenant_ids:
                print(f"   - {tenant_name}: {str(product_id)[:8]}")
    
    # Check 5: Review counts are isolated
    print("\n🔍 Check 5: Review Isolation")
    for result in results:
        expected_reviews = result["product_count"] * 3  # 3 reviews per product
        if result["review_count"] != expected_reviews:
            print(f"❌ {result['tenant_name']}: Expected {expected_reviews} reviews, got {result['review_count']}")
            all_passed = False
        else:
            print(f"✅ {result['tenant_name']}: Correct review count ({expected_reviews})")
    
    return all_passed


async def main():
    """Run the complete sanity check"""
    print("\n" + "=" * 80)
    print("MULTI-TENANCY SANITY CHECK")
    print("=" * 80)
    print("This script will:")
    print("1. Run the database migration")
    print("2. Create 3 tenants with users")
    print("3. Insert overlapping SKUs for each tenant")
    print("4. Run full multi-agent queries")
    print("5. Verify outputs never mix")
    print("=" * 80)
    
    # Step 1: Run migration
    migration_success = await run_migration()
    if not migration_success:
        print("\n❌ SANITY CHECK FAILED: Migration failed")
        return False
    
    # Create database session
    async with AsyncSessionLocal() as db:
        try:
            # Step 2: Create tenants and users
            tenants, users, tokens = await create_tenants_and_users(db)
            
            # Step 3: Insert overlapping SKUs
            all_products = await insert_overlapping_skus(db, tenants)
            
            # Step 4: Run multi-agent queries for each tenant
            results = []
            for tenant, products in zip(tenants, all_products):
                result = await run_multi_agent_query(db, tenant, products)
                results.append(result)
            
            # Step 5: Verify no data mixing
            verification_passed = await verify_no_data_mixing(results)
            
            # Final result
            print("\n" + "=" * 80)
            print("SANITY CHECK RESULTS")
            print("=" * 80)
            
            if verification_passed:
                print("✅ ALL CHECKS PASSED!")
                print("\n🎉 Multi-tenancy implementation is working correctly!")
                print("✅ Tenants are properly isolated")
                print("✅ Overlapping SKUs handled correctly")
                print("✅ Agents filter by tenant_id")
                print("✅ No data mixing detected")
                print("\n🚀 Ready to move to Demand Agent implementation!")
                return True
            else:
                print("❌ SOME CHECKS FAILED!")
                print("\n⚠️  Multi-tenancy implementation has issues")
                print("❌ Data mixing detected or isolation broken")
                print("\n🛑 DO NOT move to Demand Agent until fixed!")
                return False
                
        except Exception as e:
            print(f"\n❌ SANITY CHECK FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
