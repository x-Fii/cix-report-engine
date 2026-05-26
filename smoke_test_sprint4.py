import sys
import os
import requests
import json
import jwt
from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.models import User, DeliveryOrder, Customer, Outlet, AssetSku, Upload, CatalogItem, Region

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

API_URL = "http://127.0.0.1:8000/api/v1"

def print_pass(msg):
    print(f"{GREEN}[PASS] {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}[FAIL] {msg}{RESET}")
    sys.exit(1)

def seed_database(db: Session):
    print("--- 1. Seeding Phase ---")
    try:
        # Seed user
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, username='fii_ops', email='fii@click-ix.com', display_name='Fii Ops', initials='FO')
            db.add(user)
            
        # Ensure dependencies for DeliveryOrder
        cust = db.query(Customer).filter(Customer.id == 6).first()
        if not cust:
            cust = Customer(id=6, code='Maxis-Test', name='Maxis')
            db.add(cust)
            
        reg = db.query(Region).filter(Region.id == 1).first()
        if not reg:
            reg = Region(id=1, name='CEN')
            db.add(reg)
            
        outl = db.query(Outlet).filter(Outlet.maxis_centre_id == 1).first()
        if not outl:
            outl = Outlet(maxis_centre_id=1, customer_id=6, region_id=1, maxis_centre_name='1Borneo', type='MC', state='Sabah', address='Test', project_ref='MIGRATE-2026')
            db.add(outl)
            
        # Seed DeliveryOrder
        do = db.query(DeliveryOrder).filter(DeliveryOrder.id == 1).first()
        if not do:
            do = DeliveryOrder(
                id=1,
                do_no='DO-TEST-001',
                customer_id=6,
                maxis_centre_id=1,
                salesperson='Fii',
                bill_to='Test Bill To',
                ship_to='Test Ship To',
                status='draft'
            )
            db.add(do)
            
        # Catalog item
        catalog = db.query(CatalogItem).filter(CatalogItem.item_code == 'MHD-MP').first()
        if not catalog:
            catalog = CatalogItem(item_code='MHD-MP', type='hardware', description='Test')
            db.add(catalog)
            
        # Assets
        asset_a = db.query(AssetSku).filter(AssetSku.sku == 'TEST-UNASSIGN').first()
        if not asset_a:
            asset_a = AssetSku(sku='TEST-UNASSIGN', item_code='MHD-MP', type='MP', state='unassign', maxis_centre_id=None)
            db.add(asset_a)
        else:
            asset_a.state = 'unassign'
            asset_a.maxis_centre_id = None
            
        asset_b = db.query(AssetSku).filter(AssetSku.sku == 'TEST-DEPLOYED').first()
        if not asset_b:
            asset_b = AssetSku(sku='TEST-DEPLOYED', item_code='MHD-MP', type='MP', state='deployed', maxis_centre_id=2)
            db.add(asset_b)
        else:
            asset_b.state = 'deployed'
            asset_b.maxis_centre_id = 2
            
        db.commit()
        db.refresh(asset_a)
        db.refresh(asset_b)
        print_pass("Database baseline seeded correctly.")
        return asset_a.id, asset_b.id
    except Exception as e:
        db.rollback()
        print_fail(f"Failed to seed database: {e}")

def test_uploads(headers):
    print("\n--- 2. File Upload Test Phase ---")
    file_data = b"DUMMY_BINARY_DATA_FOR_SHA256_TEST_STRING_ABCD1234"
    
    try:
        # First POST
        res1 = requests.post(f"{API_URL}/uploads", headers=headers, files={"file": ("test.png", file_data, "image/png")})
        if res1.status_code != 201:
            print_fail(f"First upload failed: {res1.text}")
        
        upload_id_1 = res1.json().get("upload_id")
        print_pass(f"First upload succeeded with ID: {upload_id_1}")
        
        # Second POST
        res2 = requests.post(f"{API_URL}/uploads", headers=headers, files={"file": ("test_dupe.png", file_data, "image/png")})
        if res2.status_code != 201:
            print_fail(f"Second upload failed: {res2.text}")
            
        upload_id_2 = res2.json().get("upload_id")
        if upload_id_1 == upload_id_2:
            print_pass("Duplicate filtration verified! Second upload returned the same ID.")
        else:
            print_fail(f"Duplicate filtration failed! ID 1: {upload_id_1}, ID 2: {upload_id_2}")
            
        return upload_id_1
    except requests.exceptions.ConnectionError:
        print_fail("Could not connect to API server. Make sure it is running on http://127.0.0.1:8000")

def test_service_report(db: Session, headers, upload_id, asset_a_id, asset_b_id):
    print("\n--- 3. Service Report Ingestion Test Phase ---")
    
    # We must use a unique SR no if this script is run multiple times
    import time
    unique_sr_no = f"SR-TEST-{int(time.time())}"
    
    payload = {
        "sr_no": unique_sr_no,
        "do_no": "DO-TEST-001",
        "client": {
            "company": "Maxis",
            "company_address": ["Test Address"],
            "store_type": "MC",
            "store_name": "1Borneo",
            "pic_name": "John Doe",
            "pic_tel": "0123456789"
        },
        "acknowledgement": {
            "signed_by": "John Doe",
            "signature_png_upload_id": upload_id,
            "operator_email": "test@click-ix.com"
        },
        "hardware_swaps": [
            {
                "direction": "installed",
                "sku_id": asset_a_id,
                "item_code": "MHD-MP"
            },
            {
                "direction": "removed",
                "sku_id": asset_b_id,
                "item_code": "MHD-MP",
                "is_faulty": True
            }
        ]
    }
    
    res = requests.post(f"{API_URL}/operations/service-reports", headers=headers, json=payload)
    if res.status_code != 201:
        print_fail(f"Service report ingestion failed: {res.text}")
    print_pass("Service report successfully ingested.")
    
    print("\n--- 4. Assertive Verification Phase ---")
    # End the current transaction so we can see changes committed by the API
    db.rollback()
    
    asset_a = db.query(AssetSku).filter(AssetSku.id == asset_a_id).first()
    asset_b = db.query(AssetSku).filter(AssetSku.id == asset_b_id).first()
    
    fail = False
    if asset_a.state == 'deployed' and asset_a.maxis_centre_id == 1:
        print_pass(f"Asset A ({asset_a_id}) successfully updated to 'deployed' and maxis_centre_id=1.")
    else:
        print_fail(f"Asset A state incorrect. Expected deployed/1, got state: {asset_a.state}, maxis_centre_id: {asset_a.maxis_centre_id}")
        fail = True
        
    if asset_b.state == 'to be disposed' and asset_b.maxis_centre_id is None:
        print_pass(f"Asset B ({asset_b_id}) successfully updated to 'to be disposed' and maxis_centre_id=None.")
    else:
        print_fail(f"Asset B state incorrect. Expected to be disposed/None, got state: {asset_b.state}, maxis_centre_id: {asset_b.maxis_centre_id}")
        fail = True
        
    if not fail:
        print(f"\n{GREEN}ALL SPRINT 4 SMOKE TESTS PASSED!{RESET}")

def main():
    db = SessionLocal()
    try:
        asset_a_id, asset_b_id = seed_database(db)
        
        # Generate valid local JWT token
        token = jwt.encode({"email": "test@click-ix.com", "id": 1}, os.getenv("JWT_SECRET", "super-secret-key"), algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        upload_id = test_uploads(headers)
        test_service_report(db, headers, upload_id, asset_a_id, asset_b_id)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
