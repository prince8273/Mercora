"""
Script to fix all integration test execute_plan calls
"""
import re

# Files and their product variable patterns
fixes = [
    # test_end_to_end_query.py
    {
        "file": "tests/integration/test_end_to_end_query.py",
        "replacements": [
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-456"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-456",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-789"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-789",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
        ]
    },
    # test_deep_mode.py
    {
        "file": "tests/integration/test_deep_mode.py",
        "replacements": [
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-COORD-001"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-COORD-001",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-COMP-001"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-COMP-001",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-PARALLEL-001"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-PARALLEL-001",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
        ]
    },
    # test_multi_tenant_integration.py
    {
        "file": "tests/integration/test_multi_tenant_integration.py",
        "replacements": [
            {
                "old": 'query_data={"query": query_text_a, "product_sku": "SKU-TENANT-A"}',
                "new": '''query_data={
            "query": query_text_a,
            "product_sku": "SKU-TENANT-A",
            "db": db_session,
            "tenant_id": tenant_a,
            "product_ids": [product_a.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text_b, "product_sku": "SKU-TENANT-B"}',
                "new": '''query_data={
            "query": query_text_b,
            "product_sku": "SKU-TENANT-B",
            "db": db_session,
            "tenant_id": tenant_b,
            "product_ids": [product_b.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text, "product_sku": "SKU-CONTEXT-001"}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": "SKU-CONTEXT-001",
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [product.id]
        }''',
            },
            {
                "old": 'query_data={"query": query_text, "product_sku": sku}',
                "new": '''query_data={
            "query": query_text,
            "product_sku": sku,
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [p.id for p in products if p.sku == sku]
        }''',
            },
            {
                "old": 'query_data={"query": f"Analyze {sku}", "product_sku": sku}',
                "new": '''query_data={
            "query": f"Analyze {sku}",
            "product_sku": sku,
            "db": db_session,
            "tenant_id": tenant_id,
            "product_ids": [p.id for p in products if p.sku == sku]
        }''',
            },
        ]
    },
]

for fix in fixes:
    filepath = fix["file"]
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for replacement in fix["replacements"]:
        if replacement["old"] in content:
            content = content.replace(replacement["old"], replacement["new"])
            print(f"  ✓ Fixed: {replacement['old'][:50]}...")
        else:
            print(f"  ✗ Not found: {replacement['old'][:50]}...")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("\nDone!")
