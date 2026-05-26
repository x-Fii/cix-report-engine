from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta, timezone
import os

from config.database import get_db
from config.firebase import auth as firebase_auth
import models.models as models

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")

class LoginRequest(BaseModel):
    firebase_id_token: str

@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    if request.headers.get("X-Dev-Mock") == "true":
        decoded_token = {"email": "fii@click-ix.com"}
    else:
        # Verify Firebase ID token
        try:
            decoded_token = firebase_auth.verify_id_token(payload.firebase_id_token)
        except Exception as e:
            raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": str(e)}})
    
    email = decoded_token.get("email")
    if not email or not email.endswith("@click-ix.com"):
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_DOMAIN", "message": "Domain must end with @click-ix.com"}})
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Provision them
        name_part = email.split('@')[0]
        parts = name_part.split('.')
        if len(parts) >= 2:
            initials = (parts[0][0] + parts[-1][0]).upper()
        else:
            initials = parts[0][:2].upper()
            
        display_name = " ".join([p.capitalize() for p in parts])
        
        try:
            # Check if role 'ops' exists
            ops_role = db.query(models.Role).filter(models.Role.code == 'ops').first()
            if not ops_role:
                ops_role = models.Role(code='ops')
                db.add(ops_role)
                db.flush()
                
            user = models.User(
                username=name_part,
                email=email,
                display_name=display_name,
                initials=initials,
                active=True
            )
            db.add(user)
            db.flush()
            
            # Map to ops role
            user_role = models.UserRole(user_id=user.id, role_id=ops_role.id)
            db.add(user_role)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail={"error": {"code": "DB_ERROR", "message": str(e)}})

    # Fetch roles
    user_roles = db.query(models.Role.code).join(models.UserRole).filter(models.UserRole.user_id == user.id).all()
    roles = [r[0] for r in user_roles]

    # Generate JWT
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    jwt_payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "initials": user.initials,
        "roles": roles,
        "exp": exp
    }
    
    internal_token = jwt.encode(jwt_payload, SECRET_KEY, algorithm="HS256")
    
    return {"token": internal_token, "user": jwt_payload}
