"""
Admin API Endpoints
Routes:
  GET  /admin/users                    — list semua user (search + pagination)
  GET  /admin/users/{user_id}          — detail satu user
  PATCH /admin/users/{user_id}/limits  — ubah daily_limit quota user
  PATCH /admin/users/{user_id}/role    — ubah role user (promote/demote admin)
  PATCH /admin/users/{user_id}/status  — aktifkan / nonaktifkan akun user
"""
from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel, field_validator

from app.db.database import get_db
from app.db.models import User, Quota, UserRole
from app.core.security import get_current_active_user, require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─────────────────────────────────────────────
# Default plan limits
# Sesuaikan dengan PLAN_LIMITS di frontend constants.js
# ─────────────────────────────────────────────

PLAN_DAILY_ANALYSIS: dict[str, int] = {
    "free":       5,
    "pro":        50,
    "enterprise": 9999,
}

PLAN_DAILY_TOKEN: dict[str, int] = {
    "free":       50_000,
    "pro":        500_000,
    "enterprise": 10_000_000,
}

DEFAULT_DAILY_ANALYSIS = 5
DEFAULT_DAILY_TOKEN    = 50_000


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────

class QuotaOut(BaseModel):
    daily_used: int
    daily_limit: int
    daily_remaining: int
    usage_percentage: float
    total_analyses: int
    total_documents: int
    total_tokens_used: int
    # ✅ FIX 4: tambah field token limit supaya frontend bisa baca
    daily_token_limit: int
    storage_used_bytes: int
    storage_limit_bytes: int
    storage_used_mb: float


class UserAdminOut(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    plan: str
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    created_at: str
    last_login: Optional[str]
    quota: Optional[QuotaOut]


class PaginatedUsersResponse(BaseModel):
    items: list[UserAdminOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class UpdateLimitsRequest(BaseModel):
    """
    Kirim null/None = reset ke default plan.
    Kirim angka positif = set override.
    """
    plan: Optional[str] = None
    daily_analysis_limit: Optional[int] = None
    daily_token_limit: Optional[int] = None

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"free", "pro", "enterprise"}:
            raise ValueError("Plan harus berupa free, pro, atau enterprise")
        return v

    # ✅ FIX 2: tambah validator untuk daily_analysis_limit
    @field_validator("daily_analysis_limit")
    @classmethod
    def validate_analysis_limit(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Limit analisis tidak boleh negatif")
        return v

    @field_validator("daily_token_limit")
    @classmethod
    def validate_token_limit(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Limit token tidak boleh negatif")
        return v


class UpdateRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {r.value for r in UserRole}
        if v not in allowed:
            raise ValueError(f"Role harus salah satu dari: {', '.join(allowed)}")
        return v


class UpdateStatusRequest(BaseModel):
    is_active: bool


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _plan_str(user: User) -> str:
    """Ambil nilai plan sebagai string, aman untuk Enum maupun string biasa."""
    return getattr(user.plan, "value", str(user.plan))


def serialize_user(user: User, quota: Optional[Quota]) -> UserAdminOut:
    plan = _plan_str(user)
    quota_out = None
    if quota:
        quota_out = QuotaOut(
            daily_used=quota.daily_used,
            daily_limit=quota.daily_limit,
            daily_remaining=quota.daily_remaining,
            usage_percentage=quota.usage_percentage,
            total_analyses=quota.total_analyses,
            total_documents=quota.total_documents,
            total_tokens_used=quota.total_tokens_used,
            # ✅ FIX 4: sertakan daily_token_limit di response
            # Baca dari kolom quota kalau ada, fallback ke default plan
            daily_token_limit=getattr(
                quota, "daily_token_limit", None
            ) or PLAN_DAILY_TOKEN.get(plan, DEFAULT_DAILY_TOKEN),
            storage_used_bytes=quota.storage_used_bytes,
            storage_limit_bytes=quota.storage_limit_bytes,
            storage_used_mb=quota.storage_used_mb,
        )

    return UserAdminOut(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        plan=plan,
        role=getattr(user.role, "value", str(user.role)),
        is_active=user.is_active,
        is_verified=user.is_verified,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        quota=quota_out,
    )


async def get_user_or_404(user_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User dengan id '{user_id}' tidak ditemukan.",
        )
    return user


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    base_q = select(User)
    if search and search.strip():
        term = f"%{search.strip()}%"
        base_q = base_q.where(
            or_(
                User.username.ilike(term),
                User.email.ilike(term),
                User.full_name.ilike(term),
            )
        )

    total: int = (await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )).scalar_one()

    offset = (page - 1) * page_size
    users: list[User] = list(
        (await db.execute(
            base_q.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )).scalars().all()
    )

    user_ids = [u.id for u in users]
    quota_map: dict[str, Quota] = {
        q.user_id: q
        for q in (await db.execute(
            select(Quota).where(Quota.user_id.in_(user_ids))
        )).scalars().all()
    }

    return PaginatedUsersResponse(
        items=[serialize_user(u, quota_map.get(u.id)) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/users/{user_id}", response_model=UserAdminOut)
async def get_user_detail(
    user_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_or_404(user_id, db)
    quota = (await db.execute(
        select(Quota).where(Quota.user_id == user_id)
    )).scalar_one_or_none()
    return serialize_user(user, quota)


@router.patch("/users/{user_id}/limits", response_model=UserAdminOut)
async def update_user_limits(
    user_id: str,
    payload: UpdateLimitsRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_or_404(user_id, db)
    quota = (await db.execute(
        select(Quota).where(Quota.user_id == user_id)
    )).scalar_one_or_none()

    # ✅ FIX 3: cast ke Enum value kalau model pakai Enum
    if payload.plan is not None:
        try:
            from app.db.models import UserPlan  # import sesuai nama Enum plan kamu
            user.plan = UserPlan(payload.plan)
        except (ImportError, ValueError):
            # Fallback: assign string langsung kalau tidak pakai Enum
            user.plan = payload.plan

    plan = _plan_str(user)

    if not quota:
        quota = Quota(
            user_id=user_id,
            daily_limit=PLAN_DAILY_ANALYSIS.get(plan, DEFAULT_DAILY_ANALYSIS),
        )
        db.add(quota)
        await db.flush()

    # Update analysis limit
    if payload.daily_analysis_limit is not None:
        quota.daily_limit = payload.daily_analysis_limit
    else:
        # null = reset ke default plan
        quota.daily_limit = PLAN_DAILY_ANALYSIS.get(plan, DEFAULT_DAILY_ANALYSIS)

    # ✅ FIX 1: simpan token limit ke quota (kolom harus ada di model Quota)
    # Kalau kolom belum ada, lihat catatan migrasi di bawah
    if hasattr(quota, "daily_token_limit"):
        if payload.daily_token_limit is not None:
            quota.daily_token_limit = payload.daily_token_limit
        else:
            # null = reset ke default plan
            quota.daily_token_limit = PLAN_DAILY_TOKEN.get(plan, DEFAULT_DAILY_TOKEN)

    await db.commit()
    await db.refresh(quota)
    await db.refresh(user)
    return serialize_user(user, quota)


@router.patch("/users/{user_id}/role", response_model=UserAdminOut)
async def update_user_role(
    user_id: str,
    payload: UpdateRoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == str(admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa mengubah role akun Anda sendiri.",
        )

    user = await get_user_or_404(user_id, db)

    # ✅ FIX 3 (role): cast ke Enum supaya tidak crash di model Enum
    try:
        user.role = UserRole(payload.role)
    except ValueError:
        user.role = payload.role

    await db.commit()
    await db.refresh(user)

    quota = (await db.execute(
        select(Quota).where(Quota.user_id == user_id)
    )).scalar_one_or_none()
    return serialize_user(user, quota)


@router.patch("/users/{user_id}/status", response_model=UserAdminOut)
async def update_user_status(
    user_id: str,
    payload: UpdateStatusRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == str(admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa mengubah status akun Anda sendiri.",
        )

    user = await get_user_or_404(user_id, db)
    user.is_active = payload.is_active
    await db.commit()
    await db.refresh(user)

    quota = (await db.execute(
        select(Quota).where(Quota.user_id == user_id)
    )).scalar_one_or_none()
    return serialize_user(user, quota)


@router.get("/stats", tags=["Admin"])
async def admin_stats(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users  = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)  # noqa: E712
    )).scalar_one()
    admin_count  = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )).scalar_one()

    plan_rows = (await db.execute(
        select(User.plan, func.count(User.id)).group_by(User.plan)
    )).all()

    total_analyses = (await db.execute(
        select(func.coalesce(func.sum(Quota.total_analyses), 0))
    )).scalar_one()
    total_tokens = (await db.execute(
        select(func.coalesce(func.sum(Quota.total_tokens_used), 0))
    )).scalar_one()
    total_docs = (await db.execute(
        select(func.coalesce(func.sum(Quota.total_documents), 0))
    )).scalar_one()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "admins": admin_count,
            "by_plan": {getattr(r[0], "value", r[0]): r[1] for r in plan_rows},
        },
        "usage": {
            "total_analyses": int(total_analyses),
            "total_tokens_used": int(total_tokens),
            "total_documents": int(total_docs),
        },
    }