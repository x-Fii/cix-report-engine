from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(prefix="/regions", tags=["Regions"])

@router.get("", response_model=List[schemas.RegionResponse])
def get_regions(skip: int = Query(0, ge=0), limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    regions = db.query(models.Region).offset(skip).limit(limit).all()
    return regions

@router.post("", response_model=schemas.RegionResponse)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Region).filter(models.Region.name == region.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Region name already exists")
    
    db_region = models.Region(**region.model_dump())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

@router.post("/bulk", response_model=List[schemas.RegionResponse])
def create_regions_bulk(regions: List[schemas.RegionCreate], db: Session = Depends(get_db)):
    names = [r.name for r in regions]
    existing = db.query(models.Region).filter(models.Region.name.in_(names)).all()
    if existing:
        existing_names = [e.name for e in existing]
        raise HTTPException(status_code=400, detail=f"The following region names already exist: {', '.join(existing_names)}")

    db_regions = [models.Region(**region.model_dump()) for region in regions]
    db.add_all(db_regions)
    db.commit()
    
    for r in db_regions:
        db.refresh(r)
        
    return db_regions
