from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

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
