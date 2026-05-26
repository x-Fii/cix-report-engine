from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class ClientPayload(BaseModel):
    company: str
    company_address: List[str]
    store_type: str
    store_name: str
    pic_name: str
    pic_tel: str

class AcknowledgementPayload(BaseModel):
    signed_by: str
    signature_png_upload_id: int  # Must map cleanly to integer auto-increment uploads.id PK
    operator_email: str

class ServiceReportCreatePayload(BaseModel):
    sr_no: str
    do_no: str
    client: ClientPayload
    wo_number: Optional[str] = None
    remedy_number: Optional[str] = None
    diagnostic: Optional[str] = None
    action_taken: Optional[str] = None
    acknowledgement: AcknowledgementPayload

# Company (Customer) Schemas
class CompanyCreate(BaseModel):
    code: str
    name: str
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None

class CompanyResponse(CompanyCreate):
    id: int
    class Config:
        from_attributes = True

# Region Schemas
class RegionCreate(BaseModel):
    name: str

class RegionResponse(RegionCreate):
    id: int
    class Config:
        from_attributes = True

# Site (Outlet) Schemas
class SiteCreate(BaseModel):
    company_id: int
    region_id: int
    maxis_centre_name: str
    type: str
    state: str
    locality: Optional[str] = None
    address: str
    store_pic: Optional[str] = None
    contact_no: Optional[str] = None
    project_ref: str

class SiteResponse(BaseModel):
    maxis_centre_id: int
    company_id: int = Field(alias="customer_id")
    region_id: int
    maxis_centre_name: str
    type: str
    state: str
    locality: Optional[str] = None
    address: str
    store_pic: Optional[str] = None
    contact_no: Optional[str] = None
    project_ref: str
    class Config:
        from_attributes = True
        populate_by_name = True

