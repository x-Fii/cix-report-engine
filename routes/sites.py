from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.get("", response_model=List[schemas.SiteResponse])
def get_sites(skip: int = Query(0, ge=0), limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    sites = db.query(models.Outlet).offset(skip).limit(limit).all()
    return sites

def validate_site(site: schemas.SiteCreate, db: Session):
    company = db.query(models.Customer).filter(models.Customer.id == site.company_id).first()
    if not company:
        raise HTTPException(status_code=400, detail=f"Company with id {site.company_id} does not exist")
    
    region = db.query(models.Region).filter(models.Region.id == site.region_id).first()
    if not region:
        raise HTTPException(status_code=400, detail=f"Region with id {site.region_id} does not exist")

@router.post("", response_model=schemas.SiteResponse)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    validate_site(site, db)
    
    site_dict = site.model_dump()
    site_dict["customer_id"] = site_dict.pop("company_id")
    
    db_site = models.Outlet(**site_dict)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

@router.post("/bulk", response_model=List[schemas.SiteResponse])
def create_sites_bulk(sites: List[schemas.SiteCreate], db: Session = Depends(get_db)):
    for site in sites:
        validate_site(site, db)

    db_sites = []
    for site in sites:
        site_dict = site.model_dump()
        site_dict["customer_id"] = site_dict.pop("company_id")
        db_sites.append(models.Outlet(**site_dict))

    db.add_all(db_sites)
    db.commit()
    
    for s in db_sites:
        db.refresh(s)
        
    return db_sites
