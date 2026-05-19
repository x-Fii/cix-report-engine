import os
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import json

from database import get_db
import models
import schemas

app = FastAPI(title="Click-iX Report Engine Gateway", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/home/cix-1/cix-report-engine/uploads/2026/05"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/uploads", status_code=status.HTTP_201_CREATED)
async def upload_client_signature(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid extension contract.")
    
    file_bytes = await file.read()
    generated_upload_id = f"sign_{uuid.uuid4().hex[:12]}"
    stored_filename = f"{generated_upload_id}.png"
    target_absolute_path = os.path.join(UPLOAD_DIR, stored_filename)
    
    try:
        with open(target_absolute_path, "wb") as buffer:
            buffer.write(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disk I/O Error: {str(e)}")
        
    db_signature = models.Upload(
        path=target_absolute_path,
        mime=file.content_type or "image/png",
        size=len(file_bytes),
        sha256=uuid.uuid4().hex,  # Placeholder token
        uploaded_by=None
    )
    db.add(db_signature)
    db.commit()
    db.refresh(db_signature)
    
    return {"upload_id": db_signature.id, "status": "Asset written to ledger successfully"}

@app.post("/api/v1/operations/service-reports", status_code=status.HTTP_201_CREATED)
async def process_service_manifest(payload: schemas.ServiceReportCreatePayload, db: Session = Depends(get_db)):
    sig_check = db.query(models.Upload).filter(models.Upload.id == payload.acknowledgement.signature_png_upload_id).first()
    if not sig_check:
        raise HTTPException(status_code=404, detail="Signature mapping violation: ID not found in registry.")

    do_check = db.query(models.DeliveryOrder).filter(models.DeliveryOrder.do_no == payload.do_no).first()
    if not do_check:
        raise HTTPException(status_code=404, detail=f"Delivery Order reference {payload.do_no} does not exist.")

    existing_sr = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == payload.sr_no).first()
    if existing_sr:
        raise HTTPException(status_code=400, detail=f"Conflict Error: Report number {payload.sr_no} is already locked.")

    try:
        db_report = models.ServiceReport(
            sr_no=payload.sr_no,
            do_id=do_check.id,
            wo_number=payload.wo_number,
            remedy_number=payload.remedy_number,
            client_company=payload.client.company,
            client_addr_json=json.dumps(payload.client.company_address),
            store_type=payload.client.store_type,
            store_name=payload.client.store_name,
            pic_name=payload.client.pic_name,
            pic_tel=payload.client.pic_tel,
            diagnostic=payload.diagnostic,
            action_taken=payload.action_taken,
            ack_signed_by=payload.acknowledgement.signed_by,
            ack_signature_upload_id=sig_check.id
        )
        db.add(db_report)
        db.commit()
        return {"status": "Success", "message": f"Ledger entries completely synchronized for {payload.sr_no}"}
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database state breakdown: {str(err)}")

@app.get("/api/v1/operations/service-reports/{sr_no}/download")
async def extract_service_pdf(sr_no: str, db: Session = Depends(get_db)):
    report_record = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == sr_no).first()
    if not report_record:
        raise HTTPException(status_code=404, detail="Target document reference not found.")
    return {"status": "Mock Stream Pass", "msg": f"Ready to download report {sr_no}"}
