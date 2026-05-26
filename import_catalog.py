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

def clean_ram(val):
    val = str(val).strip().upper()
    if val == 'NAN' or not val: return '8GB'
    if 'GB' not in val:
        import re
        m = re.search(r'(\d+)', val)
        if m:
            val = m.group(1) + 'GB'
        else:
            return '8GB'
    
    valid_rams = {'4GB', '8GB', '16GB', '32GB', '128GB', '256GB'}
    if val in valid_rams:
        return val
    return '8GB'

def clean_storage(val):
    val = str(val).strip().upper()
    if val == 'NAN' or not val: return None
    import re
    m = re.search(r'(\d+)', val)
    if m:
        num = int(m.group(1))
        if num in [120, 128]: return '128GB'
        if num in [240, 250, 256]: return '256GB'
        if num in [500, 512]: return '512GB'
        if num in [1000, 1]: return '1TB'
        if num in [2000, 2]: return '2TB+' 
        if num <= 4: return '4GB'
        if num <= 8: return '8GB'
        if num <= 16: return '16GB'
        if num <= 32: return '32GB'
    valid_storage = {'4GB', '8GB', '16GB', '32GB', '128GB', '256GB', '512GB', '1TB', '2TB+'}
    if val in valid_storage: return val
    return None

def clean_internet(val):
    val = str(val).strip().lower()
    if val == 'nan' or not val: return None
    if 'dongle' in val: return 'Wifi Dongle'
    if 'wifi' in val: return 'Wi-Fi'
    if 'lan' in val: return 'LAN'
    if 'sim' in val or '4g' in val: return '4G SIM'
    return None

def import_media_players():
    print("\nReading media players...")
    mp_df = pd.read_csv("1 Devices Tracker(Media Player).csv", header=1)
    
    def get_item_code(val):
        val = str(val).strip()
        if not val or val.lower() == 'n/a' or val.lower() == 'nan':
            return 'MHD-MP'
        return val
        
    mp_df['clean_item_code'] = mp_df['Item Code'].apply(get_item_code)
    
    unique_items = mp_df['clean_item_code'].unique()
    catalog_payload = [{"item_code": ic, "type": "hardware", "description": "Base Media Player Unit"} for ic in unique_items]
        
    print(f"Seeding {len(catalog_payload)} base catalog items...")
    res = requests.post(f"{API_BASE}/catalog/bulk", json=catalog_payload)
    if res.status_code not in (200, 201):
        print("Failed to bulk insert catalog items:", res.text)
        sys.exit(1)
    print("Successfully seeded catalog items.")

    def is_valid_sku(val):
        val = str(val).strip()
        return bool(val and val.lower() != 'nan' and '*' not in val)

    # Filter out historical duplicates for valid hardcoded SKUs keeping the last entry
    valid_sku_mask = mp_df['SKU'].apply(is_valid_sku)
    valid_df = mp_df[valid_sku_mask].drop_duplicates(subset=['SKU'], keep='last')
    invalid_df = mp_df[~valid_sku_mask]
    
    # Recombine the dataframes
    mp_df = pd.concat([valid_df, invalid_df]).reset_index(drop=True)

    def clean_sku(val, idx):
        val = str(val).strip()
        if not val or val.lower() == 'nan' or '*' in val:
            return f"GEN-MP-2026-{idx:03d}"
        return val
        
    def clean_status(val):
        val = str(val).strip().lower()
        if val == 'assigned': return 'assigned'
        return 'unassign'
        
    players = []
    for idx, row in mp_df.iterrows():
        sku = clean_sku(row['SKU'], idx + 1)
        state = clean_status(row['Status'])
        item_code = row['clean_item_code']
        
        processor = str(row['CPU']).strip() if pd.notna(row['CPU']) else None
        if processor and processor.lower() == 'nan': processor = None
        
        anydesk = str(row['Anydesk']).strip() if pd.notna(row['Anydesk']) else None
        if anydesk and anydesk.lower() == 'nan': anydesk = None
        if anydesk and anydesk.lower() == 'n/a': anydesk = None
        
        pw = str(row['P/w']).strip() if pd.notna(row['P/w']) else None
        if pw and pw.lower() == 'nan': pw = None
        if pw and pw.lower() == 'n/a': pw = None
        
        tv = str(row['Teamviewer']).strip() if pd.notna(row['Teamviewer']) else None
        if tv and tv.lower() == 'nan': tv = None
        if tv and tv.lower() == 'n/a': tv = None
        
        internet_val = None
        if 'Internet' in row and pd.notna(row['Internet']):
            internet_val = clean_internet(row['Internet'])
            
        players.append({
            "sku": sku,
            "item_code": item_code,
            "state": state,
            "is_faulty": False,
            "maxis_centre_id": None,
            "specs": {
                "processor": processor,
                "ram": clean_ram(row['RAM']),
                "storage": clean_storage(row['Storage']),
                "internet": internet_val,
                "anydesk_id": anydesk,
                "anydesk_password": pw,
                "teamviewer_id": tv
            }
        })
        
    print(f"Migrating {len(players)} media players...")
    res = requests.post(f"{API_BASE}/assets/media-players/bulk", json=players)
    if res.status_code not in (200, 201):
        print("Failed to bulk insert media players:", res.text)
        sys.exit(1)
        
    print(f"Successfully migrated {len(res.json())} media players.")

if __name__ == "__main__":
    import_data()
    import_media_players()
