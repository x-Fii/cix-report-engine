from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(tags=["Assets"])

# 1. Bulk import base hardware definitions into catalog_items
@router.post("/catalog/bulk", response_model=List[schemas.CatalogItemResponse])
def create_catalog_bulk(items: List[schemas.CatalogItemCreate], db: Session = Depends(get_db)):
    db_items = []
    
    VALID_TYPES = {'hardware', 'service', 'bulk'}
    
    for item in items:
        if item.type not in VALID_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid catalog item type: {item.type}")
            
        # Check if exists
        existing = db.query(models.CatalogItem).filter(models.CatalogItem.item_code == item.item_code).first()
        if existing:
            continue # Skip existing to make bulk insert idempotent
            
        db_item = models.CatalogItem(**item.model_dump())
        db_items.append(db_item)
        
    db.add_all(db_items)
    db.commit()
    
    for item in db_items:
        db.refresh(item)
        
    return db_items

# 2. Bulk import media players (asset_skus and asset_pc_specs)
@router.post("/assets/media-players/bulk", response_model=List[schemas.MediaPlayerResponse])
def create_media_players_bulk(players: List[schemas.MediaPlayerCreate], db: Session = Depends(get_db)):
    VALID_STATES = {'unassign', 'assigned', 'deployed', 'to be disposed', 'returned_supplier', 'disposed'}
    VALID_RAM = {'4GB', '8GB', '16GB', '32GB', '128GB', '256GB', None}
    VALID_INTERNET = {'LAN', 'Wi-Fi', 'Wifi Dongle', '4G SIM', None}
    VALID_RAM_DDR = {'DDR3', 'DDR4', 'DDR5', 'DDR6', 'DDR7', None}
    VALID_STORAGE = {'4GB', '8GB', '16GB', '32GB', '128GB', '256GB', '512GB', '1TB', '2TB+', None}
    
    db_players = []
    
    for player in players:
        if player.state not in VALID_STATES:
            raise HTTPException(status_code=400, detail=f"Invalid state: {player.state}")
            
        if player.specs.ram not in VALID_RAM:
            raise HTTPException(status_code=400, detail=f"Invalid ram: {player.specs.ram}")
            
        if player.specs.internet not in VALID_INTERNET:
            raise HTTPException(status_code=400, detail=f"Invalid internet: {player.specs.internet}")
            
        if player.specs.ram_ddr not in VALID_RAM_DDR:
            raise HTTPException(status_code=400, detail=f"Invalid ram_ddr: {player.specs.ram_ddr}")
            
        if player.specs.storage not in VALID_STORAGE:
            raise HTTPException(status_code=400, detail=f"Invalid storage: {player.specs.storage}")
            
        # Verify item code exists in catalog and is of type hardware
        catalog_item = db.query(models.CatalogItem).filter(models.CatalogItem.item_code == player.item_code).first()
        if not catalog_item:
            raise HTTPException(status_code=400, detail=f"Catalog item {player.item_code} not found")
            
        # Verify Maxis Centre ID if provided
        if player.maxis_centre_id is not None:
            outlet = db.query(models.Outlet).filter(models.Outlet.maxis_centre_id == player.maxis_centre_id).first()
            if not outlet:
                raise HTTPException(status_code=400, detail=f"Maxis Centre ID {player.maxis_centre_id} not found")
                
        # Insert asset_skus
        db_sku = models.AssetSku(
            sku=player.sku,
            item_code=player.item_code,
            type='MP', # We are creating media players
            state=player.state,
            is_faulty=player.is_faulty,
            maxis_centre_id=player.maxis_centre_id
        )
        db.add(db_sku)
        db.flush() # Flush to get db_sku.id generated within transaction
        
        # Insert asset_pc_specs
        db_specs = models.AssetPcSpec(
            sku_id=db_sku.id,
            processor=player.specs.processor,
            ram=player.specs.ram,
            ram_ddr=player.specs.ram_ddr,
            storage=player.specs.storage,
            internet=player.specs.internet,
            anydesk_id=player.specs.anydesk_id,
            anydesk_password=player.specs.anydesk_password,
            teamviewer_id=player.specs.teamviewer_id,
            cix_pic=player.specs.cix_pic
        )
        db.add(db_specs)
        
        db_players.append(db_sku)
        
    db.commit()
    
    for player in db_players:
        db.refresh(player)
        
    return db_players