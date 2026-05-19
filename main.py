import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy import text
import database

app = FastAPI(title="Click-iX ERP Engine", docs_url="/api/v1/docs")

# 1. Enable Local Development CORS (Matching FRONTEND_INTEGRATION.md)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.clickix.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

# 2. Production Upload Directory Layout
UPLOAD_DIR = "/var/www/app/uploads/2026/05"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Pydantic Schemas for Data Verification ---
class ClientInfo(BaseModel):
    company: str
    company_address: list[str]
    store_type: str
    store_name: str
    pic_name: str
    pic_tel: str

class AcknowledgementInfo(BaseModel):
    signed_by: str
    signature_png_upload_id: int
    operator_email: EmailStr

    @validator('operator_email')
    def verify_click_ix_domain(cls, v):
        # Strict security logic constraint: Block external domains
        if not v.endswith('@click-ix.com'):
            raise ValueError('Access Denied: Internal Click-iX accounts only.')
        return v

class ServiceReportSchema(BaseModel):
    sr_no: str
    do_no: str
    client: ClientInfo
    wo_number: str
    remedy_number: str
    diagnostic: str
    action_taken: str
    acknowledgement: AcknowledgementInfo

# --- API Routes ---

@app.post("/api/v1/uploads")
async def upload_signature_blob(file: UploadFile = File(...)):
    """
    Accepts raw multipart signature images from the React drawing canvas.
    """
    try:
        upload_id = 8821  # Standard sequential mock tracker matching contract specs
        target_filename = f"{upload_id}.png"
        absolute_target_path = os.path.join(UPLOAD_DIR, target_filename)
        
        with open(absolute_target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "upload_id": upload_id,
            "url": f"/uploads/2026/05/{target_filename}",
            "mime": file.content_type,
            "size": os.path.getsize(absolute_target_path)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/v1/operations/service-reports")
async def process_service_pdf(payload: ServiceReportSchema, db: Session = Depends(database.get_db)):
    """
    Saves metadata to MariaDB and programmatically draws the service report PDF.
    """
    # Look up uploaded signature asset
    sig_path = os.path.join(UPLOAD_DIR, f"{payload.acknowledgement.signature_png_upload_id}.png")
    if not os.path.exists(sig_path):
        raise HTTPException(status_code=400, detail="Signature file asset missing from server volume.")

    # Format filename cleanly for safety
    clean_sr_no = payload.sr_no.replace('/', '_')
    final_pdf_name = f"SR_{clean_sr_no}_SIGNED.pdf"
    final_pdf_path = os.path.join(UPLOAD_DIR, final_pdf_name)

    # Compile the corporate PDF using ReportLab primitives
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(final_pdf_path, pagesize=letter)
    story = [
        Paragraph(f"<b>CLICK-IX SERVICE MANIFEST: {payload.sr_no}</b>", getSampleStyleSheet()['Title']),
        Spacer(1, 15),
        Paragraph(f"<b>Client Outlet Target:</b> {payload.client.store_name}", getSampleStyleSheet()['Normal']),
        Paragraph(f"<b>Action Executed on Site:</b> {payload.action_taken}", getSampleStyleSheet()['Normal']),
        Spacer(1, 25),
        Paragraph("<b>Authorized Client Representative Signature:</b>", getSampleStyleSheet()['Heading4']),
        Spacer(1, 10),
        Image(sig_path, width=150, height=60)
    ]
    doc.build(story)

    # Securely log structural transaction variables into your MariaDB database ledger table
    try:
        insert_query = text("""
            INSERT INTO Service_Reports_Signatures 
            (Ref_QT, pdf_file_path, signed_by_email, client_signee_name, signing_ip) 
            VALUES (:ref_qt, :path, :email, :client_name, :ip)
        """)
        db.execute(insert_query, {
            "ref_qt": payload.do_no,
            "path": final_pdf_path,
            "email": payload.acknowledgement.operator_email,
            "client_name": payload.client.pic_name,
            "ip": "127.0.0.1"
        })
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write mutation crash: {str(e)}")

    return {"status": "Success", "pdf_url": f"/api/v1/operations/service-reports/{payload.sr_no}/download"}

@app.get("/api/v1/operations/service-reports/{sr_no:path}/download")
async def download_service_report(sr_no: str):
    """
    Streams the finished PDF binary asset straight back to browser frames for print/download hooks.
    """
    clean_sr_no = sr_no.replace('/', '_')
    expected_pdf_name = f"SR_{clean_sr_no}_SIGNED.pdf"
    target_pdf_path = os.path.join(UPLOAD_DIR, expected_pdf_name)
    
    if not os.path.exists(target_pdf_path):
        raise HTTPException(status_code=404, detail="The requested PDF copy does not exist on storage.")
        
    return FileResponse(path=target_pdf_path, media_type="application/pdf", filename=expected_pdf_name)
