import os
import uuid
import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from config.database import get_db
import models.models as models

router = APIRouter(prefix="/uploads", tags=["Uploads"])

BASE_UPLOAD_DIR = "/home/cix-1/cix-report-engine/uploads"

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.png', '.jpg', '.jpeg', '.pdf')):
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_FAILED", "message": "Invalid extension contract."}})
    
    file_bytes = await file.read()
    
    # Compute SHA256 hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Check if hash already exists in db
    existing_upload = db.query(models.Upload).filter(models.Upload.sha256 == file_hash).first()
    if existing_upload:
        # Generate URL from path or just return existing
        return {"upload_id": existing_upload.id, "message": "Duplicate file detected. Returning existing upload reference."}
    
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
        
    uploaded_by_id = request.state.user.get("id", 1) if hasattr(request.state, "user") and isinstance(request.state.user, dict) else None
    
    db_upload = models.Upload(
        path=target_absolute_path,
        mime=file.content_type or "application/octet-stream",
        size=len(file_bytes),
        sha256=file_hash,
        uploaded_by=uploaded_by_id
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    
    return {"upload_id": db_upload.id, "url": f"/uploads/{year}/{month}/{stored_filename}"}
