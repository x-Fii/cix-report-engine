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

class HardwareSwapPayload(BaseModel):
    direction: str # 'removed' or 'installed'
    sku_id: int
    item_code: str
    reason: Optional[str] = None
    is_faulty: Optional[bool] = False

class ServiceReportCreatePayload(BaseModel):
    sr_no: str
    do_no: str
    ticket_id: Optional[int] = None
    client: ClientPayload
    wo_number: Optional[str] = None
    remedy_number: Optional[str] = None
    diagnostic: Optional[str] = None
    action_taken: Optional[str] = None
    acknowledgement: AcknowledgementPayload
    hardware_swaps: Optional[List[HardwareSwapPayload]] = []

# Ticket Schemas
class TicketCreate(BaseModel):
    ticket_no: str
    maxis_centre_id: int
    category: str
    priority: Optional[str] = 'Medium'
    status: Optional[str] = 'open'
    description: Optional[str] = None

class TicketResponse(TicketCreate):
    id: int
    created_by: int
    class Config:
        from_attributes = True

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

# Catalog Item Schemas
class CatalogItemCreate(BaseModel):
    item_code: str
    type: str
    description: str
    default_uom: Optional[str] = 'UNIT'
    default_unit_price: Optional[float] = 0.00
    default_tax_code: Optional[str] = 'S'
    active: Optional[bool] = True

class CatalogItemResponse(CatalogItemCreate):
    id: int
    class Config:
        from_attributes = True

# MediaPlayer Specs Schema
class MediaPlayerSpecCreate(BaseModel):
    processor: Optional[str] = None
    ram: Optional[str] = None
    ram_ddr: Optional[str] = None
    storage: Optional[str] = None
    internet: Optional[str] = None
    anydesk_id: Optional[str] = None
    anydesk_password: Optional[str] = None
    teamviewer_id: Optional[str] = None
    cix_pic: Optional[str] = None

# MediaPlayer Sku Schema
class MediaPlayerCreate(BaseModel):
    sku: str
    item_code: str
    state: str = 'unassign'
    is_faulty: Optional[bool] = False
    maxis_centre_id: Optional[int] = None
    specs: MediaPlayerSpecCreate

class MediaPlayerResponse(BaseModel):
    id: int
    sku: str
    item_code: str
    type: str
    state: str
    is_faulty: bool
    maxis_centre_id: Optional[int]
    class Config:
        from_attributes = True

