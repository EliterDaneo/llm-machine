"""
Authentication API Endpoints
Routes: /auth/register, /auth/login, /auth/refresh, /auth/me, /auth/logout
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, field_validator
import re

from app.db.database import get_db
from app.db.models import User, Quota, UserPlan
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username harus 3-30 karakter")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username hanya boleh huruf, angka, dan underscore")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        
        # --- Perbaikan untuk mencegah error Bcrypt ---
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password terlalu panjang (maksimal 72 bytes/karakter)")
        # ---------------------------------------------
        
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password harus mengandung minimal 1 huruf kapital")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password harus mengandung minimal 1 angka")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username harus 3-30 karakter")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username hanya boleh huruf, angka, dan underscore")
        return v.lower()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password baru minimal 8 karakter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password baru harus mengandung minimal 1 huruf kapital")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password baru harus mengandung minimal 1 angka")
        return v


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def user_to_dict(user: User, quota: Optional[Quota] = None) -> dict:
    """Serialize user model to response dict."""
    data = {
        "id": str(user.id), # PERBAIKAN: Ubah UUID object ke string untuk JSON serialization
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "plan": getattr(user.plan, "value", user.plan),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }
    
    if quota:
        data["quota"] = {
            "daily_used": quota.daily_used,
            "daily_limit": quota.daily_limit,
            "daily_remaining": quota.daily_remaining,
            "usage_percentage": quota.usage_percentage,
            "total_analyses": quota.total_analyses,
            "total_documents": quota.total_documents,
            "storage_used_mb": quota.storage_used_mb,
        }
        
    return data


# PERBAIKAN: Ubah type hint user_id dari int menjadi str
async def get_user_with_quota(user_id: str, db: AsyncSession):
    """Load user with their quota."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return None, None

    quota_result = await db.execute(select(Quota).where(Quota.user_id == user_id))
    quota = quota_result.scalar_one_or_none()

    return user, quota


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    existing_email = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar. Gunakan email lain atau login.",
        )

    existing_username = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username sudah digunakan. Pilih username lain.",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        plan=UserPlan.FREE,
    )
    db.add(user)
    await db.flush()

    quota = Quota(
        user_id=user.id,
        daily_limit=settings.FREE_QUOTA_DAILY,
        storage_limit_bytes=50 * 1024 * 1024,
    )
    db.add(quota)
    await db.commit()
    await db.refresh(user)
    await db.refresh(quota)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "message": "Akun berhasil dibuat! Selamat datang di PDF Intelligence.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_to_dict(user, quota),
    }


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda dinonaktifkan. Hubungi support.",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    quota_result = await db.execute(select(Quota).where(Quota.user_id == user.id))
    quota = quota_result.scalar_one_or_none()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_to_dict(user, quota),
    }


@router.post("/refresh")
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    token_data = decode_token(payload.refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid untuk refresh.",
        )

    user_id = token_data.get("sub")
    
    # PERBAIKAN: Hapus casting int(user_id) karena user_id sekarang berupa string UUID
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan atau tidak aktif.",
        )

    new_access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user profile with quota."""
    quota_result = await db.execute(
        select(Quota).where(Quota.user_id == current_user.id)
    )
    quota = quota_result.scalar_one_or_none()
    return user_to_dict(current_user, quota)


@router.put("/me")
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile (name, username)."""
    if payload.username and payload.username != current_user.username:
        existing = await db.execute(
            select(User).where(User.username == payload.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username sudah digunakan.",
            )
        current_user.username = payload.username

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    await db.commit()
    await db.refresh(current_user)

    return {"message": "Profil berhasil diperbarui", "user": user_to_dict(current_user)}


@router.put("/me/password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password saat ini salah.",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password baru harus berbeda dari password saat ini.",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    return {"message": "Password berhasil diperbarui."}


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: deactivate user account."""
    current_user.is_active = False
    await db.commit()
    return {"message": "Akun berhasil dinonaktifkan."}