import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import jwt

from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.regions import router as regions_router
from routes.sites import router as sites_router
from routes.assets import router as assets_router
from routes.uploads import router as uploads_router
from routes.service_reports import router as service_reports_router
from routes.tickets import router as tickets_router

app = FastAPI(title="Click-iX Report Engine Gateway", version="1.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(regions_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(service_reports_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")

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
