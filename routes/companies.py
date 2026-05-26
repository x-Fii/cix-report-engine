from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import List
from datetime import date, timedelta
from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/alerts/expiring", response_model=List[schemas.CompanyResponse])
def get_expiring_licenses(db: Session = Depends(get_db)):
    today = date.today()
    # Using 90 days as an approximation for 3 months
    three_months_from_now = today + timedelta(days=90)
    
    companies = db.query(models.Customer).filter(
        models.Customer.license_expiry.isnot(None),
        models.Customer.license_expiry >= today,
        models.Customer.license_expiry <= three_months_from_now
    ).order_by(asc(models.Customer.license_expiry)).all()
    
    return companies

@router.get("", response_model=List[schemas.CompanyResponse])
def get_companies(skip: int = Query(0, ge=0), limit: int = Query(50, le=100), db: Session = Depends(get_db)):
    companies = db.query(models.Customer).offset(skip).limit(limit).all()
    return companies

@router.post("", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Customer).filter(models.Customer.code == company.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company code already exists")
    
    db_company = models.Customer(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.post("/bulk", response_model=List[schemas.CompanyResponse])
def create_companies_bulk(companies: List[schemas.CompanyCreate], db: Session = Depends(get_db)):
    codes = [c.code for c in companies]
    existing = db.query(models.Customer).filter(models.Customer.code.in_(codes)).all()
    if existing:
        existing_codes = [e.code for e in existing]
        raise HTTPException(status_code=400, detail=f"The following company codes already exist: {', '.join(existing_codes)}")

    db_companies = [models.Customer(**company.model_dump()) for company in companies]
    db.add_all(db_companies)
    db.commit()
    
    for c in db_companies:
        db.refresh(c)
        
    return db_companies
