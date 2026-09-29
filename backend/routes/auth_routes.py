
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.database_models import User
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

security = HTTPBearer()


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: str = "viewer"
    phc_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ============================================================
# REGISTER
# ============================================================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    # Check email
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # Allowed roles
    allowed_roles = {
        "admin",
        "district_officer",
        "phc_manager",
        "viewer",
    }

    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    # Create user
    user = User(
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=request.role,
        phc_id=request.phc_id,
        active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phc_id": user.phc_id,
            "active": user.active,
        },
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create JWT
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phc_id": user.phc_id,
            "active": user.active,
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = int(user_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    return user


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def require_roles(*allowed_roles):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker


# ============================================================
# CURRENT USER ENDPOINT
# ============================================================

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "phc_id": current_user.phc_id,
            "active": current_user.active,
        },
    }