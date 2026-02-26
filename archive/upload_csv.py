"""Simple CSV upload script"""
import requests
import sys
import time
from pathlib import Path


def upload_products(csv_file_path):
    """Upload products CSV file"""
    url = "http://localhost:8000/api/v1/ingestion/upload/products"
    
    if not Path(csv_file_path).exists():
        print(f"❌ File not found: {csv_file_path}")
        return None
    
    print(f"📤 Uploading products from: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (Path(csv_file_path).name, f, 'text/csv')}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Upload successful!")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Records: {data['records_processed']}")
            return data['job_id']
        else:
            print(f"\n❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend server!")
        print("   Make sure the server is running on http://localhost:8000")
        print("   Start with: python -m uvicorn src.main:app --reload")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def upload_reviews(csv_file_path):
    """Upload reviews CSV file"""
    url = "http://localhost:8000/api/v1/ingestion/upload/reviews"
    
    if not Path(csv_file_path).exists():
        print(f"❌ File not found: {csv_file_path}")
        return None
    
    print(f"📤 Uploading reviews from: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'rb') as f:
            files = {'file': (Path(csv_file_path).name, f, 'text/csv')}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Upload successful!")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Records: {data['records_processed']}")
            return data['job_id']
        else:
            print(f"\n❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend server!")
        print("   Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def check_job_status(job_id):
    """Check upload job status"""
    url = f"http://localhost:8000/api/v1/ingestion/status/{job_id}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Job Status:")
            print(f"   Status: {data['status']}")
            print(f"   Records Ingested: {data['records_ingested']}")
            print(f"   Records Validated: {data['records_validated']}")
            print(f"   Records Rejected: {data['records_rejected']}")
            
            if data['errors']:
                print(f"\n⚠️  Errors:")
                for error in data['errors'][:5]:  # Show first 5 errors
                    print(f"   - {error}")
                if len(data['errors']) > 5:
                    print(f"   ... and {len(data['errors']) - 5} more errors")
            
            return data['status']
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None


def create_sample_products_csv():
    """Create a sample products CSV file"""
    filename = "sample_products.csv"
    content = """sku,name,category,price,currency,marketplace,inventory_level
LAPTOP-2024,Ultra Gaming Laptop,Electronics,2499.99,USD,Amazon,15
MOUSE-2024,Wireless Gaming Mouse,Electronics,79.99,USD,Amazon,200
KEYBOARD-2024,Mechanical Keyboard RGB,Electronics,149.99,USD,eBay,75
MONITOR-2024,4K Gaming Monitor,Electronics,599.99,USD,Amazon,30
CHAIR-2024,Gaming Chair Pro,Furniture,399.99,USD,Walmart,40
DESK-2024,Standing Desk Electric,Furniture,799.99,USD,Amazon,20
WEBCAM-2024,HD Webcam 1080p,Electronics,89.99,USD,eBay,150
MIC-2024,USB Microphone,Electronics,129.99,USD,Amazon,80
LIGHT-2024,LED Ring Light,Electronics,49.99,USD,Amazon,120
CABLE-2024,USB-C Cable 6ft,Electronics,19.99,USD,Amazon,500"""
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Created sample file: {filename}")
    return filename


def create_sample_reviews_csv():
    """Create a sample reviews CSV file"""
    filename = "sample_reviews.csv"
    content = """product_sku,rating,review_text,reviewer_name,review_date
LAPTOP-2024,5,Excellent laptop! Very fast and powerful.,John Doe,2026-02-15
LAPTOP-2024,4,Good laptop but a bit expensive.,Jane Smith,2026-02-16
MOUSE-2024,5,Best mouse I've ever used!,Mike Johnson,2026-02-17
MOUSE-2024,5,Very comfortable and responsive.,Sarah Williams,2026-02-18
KEYBOARD-2024,4,Great keyboard with nice RGB lighting.,Tom Brown,2026-02-17
MONITOR-2024,5,Amazing picture quality!,Lisa Davis,2026-02-16
CHAIR-2024,4,Comfortable but assembly was difficult.,Robert Wilson,2026-02-15
DESK-2024,5,Perfect standing desk!,Emily Taylor,2026-02-18
WEBCAM-2024,3,Decent quality for the price.,David Anderson,2026-02-17
MIC-2024,5,Crystal clear audio!,Jennifer Martinez,2026-02-16"""
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Created sample file: {filename}")
    return filename


def main():
    """Main function"""
    print("="*60)
    print("CSV FILE UPLOADER")
    print("="*60)
    
    if len(sys.argv) > 1:
        # File path provided as argument
        file_path = sys.argv[1]
        file_type = sys.argv[2] if len(sys.argv) > 2 else "products"
        
        if file_type == "products":
            job_id = upload_products(file_path)
        elif file_type == "reviews":
            job_id = upload_reviews(file_path)
        else:
            print(f"❌ Unknown file type: {file_type}")
            print("   Use 'products' or 'reviews'")
            return
        
        if job_id:
            print("\n⏳ Processing... (waiting 3 seconds)")
            time.sleep(3)
            check_job_status(job_id)
            
            print("\n" + "="*60)
            print("✅ Upload complete!")
            print("="*60)
            print("\n📱 View your data:")
            print("   Dashboard: http://localhost:3000/dashboard")
            print("   API Stats: http://localhost:8000/api/v1/dashboard/stats")
            print("\n💡 Dashboard will auto-refresh in 30 seconds")
    
    else:
        # Interactive mode
        print("\nWhat would you like to do?")
        print("1. Upload products CSV")
        print("2. Upload reviews CSV")
        print("3. Create sample products CSV")
        print("4. Create sample reviews CSV")
        print("5. Upload sample products (create + upload)")
        print("6. Upload sample reviews (create + upload)")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            file_path = input("Enter products CSV file path: ").strip()
            job_id = upload_products(file_path)
            
        elif choice == "2":
            file_path = input("Enter reviews CSV file path: ").strip()
            job_id = upload_reviews(file_path)
            
        elif choice == "3":
            create_sample_products_csv()
            return
            
        elif choice == "4":
            create_sample_reviews_csv()
            return
            
        elif choice == "5":
            file_path = create_sample_products_csv()
            print()
            job_id = upload_products(file_path)
            
        elif choice == "6":
            file_path = create_sample_reviews_csv()
            print()
            job_id = upload_reviews(file_path)
            
        else:
            print("❌ Invalid choice!")
            return
        
        if job_id:
            print("\n⏳ Processing... (waiting 3 seconds)")
            time.sleep(3)
            check_job_status(job_id)
            
            print("\n" + "="*60)
            print("✅ Upload complete!")
            print("="*60)
            print("\n📱 View your data:")
            print("   Dashboard: http://localhost:3000/dashboard")
            print("   API Stats: http://localhost:8000/api/v1/dashboard/stats")
            print("\n💡 Dashboard will auto-refresh in 30 seconds")


if __name__ == "__main__":
    main()
