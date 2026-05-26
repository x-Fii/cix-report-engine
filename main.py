import os
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timezone
import json

from config.database import get_db
import models.models as models
import models.schemas as schemas
from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.regions import router as regions_router
from routes.sites import router as sites_router

app = FastAPI(title="Click-iX Report Engine Gateway", version="1.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(regions_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Authentication Gate
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key") # Use proper secret in prod

async def verify_jwt_token(request: Request):
    # Skip auth for these paths
    if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/otp-request", "/docs", "/openapi.json"]:
        return

    # Extract Auth Header manually since we're using it as a global dependency or middleware-like check
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": {"code": "UNAUTHENTICATED", "message": "Missing or invalid token"}})
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode JWT - In prod, this would verify against Firebase/Supabase public keys
        # For now, we'll assume a local verification or bypass signature if just testing
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
        email = payload.get("email")
        
        if not email or not email.endswith("@click-ix.com"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": {"code": "FORBIDDEN_ROLE", "message": "Domain not authorized"}})
            
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": {"code": "UNAUTHENTICATED", "message": "Token expired"}})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": {"code": "UNAUTHENTICATED", "message": "Invalid token"}})

# We can enforce verify_jwt_token globally using dependencies
app.router.dependencies.append(Depends(verify_jwt_token))

# Ensure all file upload handlers explicitly target and save files directly inside /home/cix-1/cix-report-engine/uploads
BASE_UPLOAD_DIR = "/home/cix-1/cix-report-engine/uploads"

@app.post("/api/v1/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_FAILED", "message": "Invalid extension contract."}})
    
    file_bytes = await file.read()
    
    # Store directly in /uploads/[YYYY]/[MM]/ as per contract
    current_date = datetime.now(timezone.utc)
    year = current_date.strftime("%Y")
    month = current_date.strftime("%m")
    
    upload_dir = os.path.join(BASE_UPLOAD_DIR, year, month)
    os.makedirs(upload_dir, exist_ok=True)
    
    generated_upload_id = uuid.uuid4().hex[:12]
    ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{generated_upload_id}{ext}"
    target_absolute_path = os.path.join(upload_dir, stored_filename)
    
    try:
        with open(target_absolute_path, "wb") as buffer:
            buffer.write(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "SERVER_ERROR", "message": f"Disk I/O Error: {str(e)}"}})
        
    db_upload = models.Upload(
        path=target_absolute_path,
        mime=file.content_type or "application/octet-stream",
        size=len(file_bytes),
        sha256=uuid.uuid4().hex,  # Placeholder token
        uploaded_by=None # To be mapped with request.state.user later
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    
    return {"upload_id": db_upload.id, "url": f"/uploads/{year}/{month}/{stored_filename}"}

@app.post("/api/v1/operations/service-reports", status_code=status.HTTP_201_CREATED)
async def process_service_manifest(request: Request, payload: schemas.ServiceReportCreatePayload, db: Session = Depends(get_db)):
    sig_check = db.query(models.Upload).filter(models.Upload.id == payload.acknowledgement.signature_png_upload_id).first()
    if not sig_check:
        raise HTTPException(status_code=404, detail={"error": {"code": "SR_PHOTOS_MISSING", "message": "Signature mapping violation: ID not found in registry."}})

    do_check = db.query(models.DeliveryOrder).filter(models.DeliveryOrder.do_no == payload.do_no).first()
    if not do_check:
        raise HTTPException(status_code=404, detail={"error": {"code": "SR_DO_MISMATCH", "message": f"Delivery Order reference {payload.do_no} does not exist."}})

    existing_sr = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == payload.sr_no).first()
    if existing_sr:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_FAILED", "message": f"Conflict Error: Report number {payload.sr_no} is already locked."}})

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
            before_photos_json="[]",
            after_photos_json="[]",
            ack_signed_by=payload.acknowledgement.signed_by,
            ack_signature_upload_id=sig_check.id,
            ack_signed_at=datetime.now(timezone.utc),
            created_by=request.state.user.get("id", 1) if hasattr(request.state, "user") and isinstance(request.state.user, dict) else 1
        )
        db.add(db_report)
        db.commit()
        return {"status": "Success", "message": f"Ledger entries completely synchronized for {payload.sr_no}"}
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": {"code": "SERVER_ERROR", "message": f"Database state breakdown: {str(err)}"}})

@app.get("/api/v1/operations/service-reports/{sr_no}/download")
async def extract_service_pdf(sr_no: str, db: Session = Depends(get_db)):
    report_record = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == sr_no).first()
    if not report_record:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Target document reference not found."}})
    return {"status": "Mock Stream Pass", "msg": f"Ready to download report {sr_no}"}
