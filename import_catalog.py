import pandas as pd
import requests
import sys

API_BASE = "http://127.0.0.1:8000/api/v1"

def clean_state(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    mapping = {
        "KL": "Kuala Lumpur",
        "N. Sembilan": "Negeri Sembilan",
        "Perlis": "Perlis",
        "Perlis ": "Perlis"
    }
    return mapping.get(val, val)

def clean_type(val):
    if pd.isna(val):
        return None
    val = str(val).strip().upper()
    mapping = {
        "KIOSK": "Kiosk",
        "FLAGSHIP": "Flagship",
        "MEP LITE": "MEP Lite",
        "MC": "MC",
        "MC+": "MC+",
        "MEP": "MEP"
    }
    return mapping.get(val, "MC") # default to MC if unknown to avoid constraint fail

def get_region_code(val):
    if pd.isna(val):
        return None
    val = str(val).strip().upper()
    if val == "EAST COAST": return "EAC"
    if val == "EAST MALAYSIA": return "EMA"
    return val[:3]

def import_data():
    print("Reading data...")
    # 1. Client Registry
    client_df = pd.read_csv("1 City Screen Tracker 2026 (1)(Master Tracker).csv", header=1)
    
    # Drop rows where Brand is empty
    client_df = client_df.dropna(subset=['Brand'])
    
    companies = []
    seen_brands = set()
    for _, row in client_df.iterrows():
        brand = str(row['Brand']).strip()
        if brand in seen_brands:
            continue
        seen_brands.add(brand)
        
        name = row['Billing Detail'] if pd.notna(row['Billing Detail']) else brand
        
        exp_date = None
        if pd.notna(row['Exp']):
            try:
                # Convert date explicitly specifying format or rely on infer
                parsed = pd.to_datetime(row['Exp'], errors='coerce', dayfirst=True)
                if pd.notna(parsed):
                    exp_date = parsed.strftime('%Y-%m-%d')
            except:
                pass
                
        companies.append({
            "code": brand,
            "name": str(name).strip(),
            "license_expiry": exp_date
        })
        
    print(f"Migrating {len(companies)} companies...")
    res = requests.post(f"{API_BASE}/companies/bulk", json=companies)
    if res.status_code not in (200, 201):
        print("Failed to bulk insert companies:", res.text)
        sys.exit(1)
        
    company_records = res.json()
    company_lookup = {c['code']: c['id'] for c in company_records}
    print(f"Successfully migrated {len(company_records)} companies.")

    # 2. Regions
    store_df = pd.read_csv("Maxis - Asset Listing Form(Store Listing ).csv")
    
    # Extract unique regions and drop NA
    regions_raw = store_df['Region'].dropna().unique()
    
    regions_payload = []
    region_code_map = {}
    for r in regions_raw:
        code = get_region_code(r)
        if code and code not in region_code_map.values():
            regions_payload.append({"name": code})
            region_code_map[r] = code
            
    print(f"Migrating {len(regions_payload)} regions...")
    res = requests.post(f"{API_BASE}/regions/bulk", json=regions_payload)
    if res.status_code not in (200, 201):
        print("Failed to bulk insert regions:", res.text)
        sys.exit(1)
        
    region_records = res.json()
    region_id_lookup = {r['name']: r['id'] for r in region_records}
    print(f"Successfully migrated {len(region_records)} regions.")

    # 3. Outlets
    outlets = []
    store_unique = store_df.dropna(subset=['Maxis Centre', 'Region', 'State']).drop_duplicates(subset=['Maxis Centre'])
    
    maxis_company_id = company_lookup.get("Maxis")
    if not maxis_company_id:
        print("Error: 'Maxis' company not found in database.")
        sys.exit(1)
        
    for _, row in store_unique.iterrows():
        region_code = get_region_code(row['Region'])
        region_id = region_id_lookup.get(region_code)
        
        state_val = clean_state(row['State'])
        type_val = clean_type(row['Type'])
        
        address = str(row['Address']).strip() if pd.notna(row['Address']) else 'N/A'
        
        outlets.append({
            "company_id": maxis_company_id,
            "region_id": region_id,
            "maxis_centre_name": str(row['Maxis Centre']).strip(),
            "type": type_val,
            "state": state_val,
            "locality": str(row['Locality']).strip() if pd.notna(row['Locality']) else None,
            "address": address,
            "store_pic": str(row['PIC']).strip() if pd.notna(row['PIC']) else None,
            "contact_no": str(row['Contact No.']).strip() if pd.notna(row['Contact No.']) else None,
            "project_ref": "MIGRATE-2026"
        })

    print(f"Migrating {len(outlets)} outlets...")
    res = requests.post(f"{API_BASE}/sites/bulk", json=outlets)
    if res.status_code not in (200, 201):
        print("Failed to bulk insert sites:", res.text)
        sys.exit(1)
        
    print(f"Successfully migrated {len(res.json())} outlets.")

if __name__ == "__main__":
    import_data()
