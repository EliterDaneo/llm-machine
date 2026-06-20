"""
Documents API Endpoints — MySQL compatible, UUID primary keys
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
import uuid

from app.db.database import get_db
from app.db.models import User, Quota, Document, AnalysisResult, ChatHistory
from app.core.security import get_current_active_user
from app.core.config import settings
# from app.services.pdf_extractor import pdf_extractor
from app.services.document_extractor import document_extractor, SUPPORTED_EXTENSIONS
from app.services.ai_orchestrator import ai_orchestrator, AnalysisMode

TOKEN_COST_PER_ANALYSIS = 50000

router = APIRouter(prefix="/documents", tags=["Documents"])


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    document_id: str          # UUID string
    # PERBAIKAN: Gunakan Optional agar tidak error 422 jika frontend mengirim null
    analysis_type: Optional[str] = "summary" 
    custom_prompt: Optional[str] = None


class ChatRequest(BaseModel):
    document_id: str          # UUID string
    message: str
    session_id: Optional[str] = None


class ChatFeedbackRequest(BaseModel):
    feedback: str             # "like" | "dislike"


# ─────────────────────────────────────────────
# Quota Helpers
# ─────────────────────────────────────────────

async def get_user_quota(user: User, db: AsyncSession) -> Quota:
    result = await db.execute(select(Quota).where(Quota.user_id == user.id))
    quota = result.scalar_one_or_none()
    if not quota:
        plan_limits = {
            "free": settings.FREE_QUOTA_DAILY,
            "pro": settings.PRO_QUOTA_DAILY,
            "enterprise": settings.ENTERPRISE_QUOTA_DAILY,
        }
        quota = Quota(
            user_id=user.id,
            daily_limit=plan_limits.get(user.plan, settings.FREE_QUOTA_DAILY),
        )
        db.add(quota)
        await db.commit()
        await db.refresh(quota)
    return quota


async def check_and_consume_quota(user: User, quota: Quota, db: AsyncSession):
    """
    Logika quota baru (dua lapis):
 
    Lapis 1 — Cek daily_analysis (hitungan per analisis):
      • Kalau daily_used < daily_limit  → lanjut normal, tambah daily_used + 1
      • Kalau daily_used >= daily_limit → masuk mode token-budget (lapis 2)
 
    Lapis 2 — Cek token budget (total_tokens_used vs token_daily_limit):
      • Kalau sisa token >= TOKEN_COST_PER_ANALYSIS → izinkan, TIDAK tambah daily_used
        (supaya counter analisis tidak overflow — ini sudah "extra" dari token)
      • Kalau token juga habis → 429 dengan pesan yang menjelaskan kedua limit habis
 
    Reset harian: kalau sudah hari baru, reset daily_used + daily_reset_at dulu.
    """
    from datetime import datetime, timezone
    from fastapi import HTTPException, status
 
    now = datetime.now(timezone.utc)
 
    # --- Reset harian kalau sudah hari baru ---
    reset = quota.daily_reset_at
    if reset.tzinfo is None:
        reset = reset.replace(tzinfo=timezone.utc)
    if reset.date() < now.date():
        quota.daily_used = 0
        quota.daily_reset_at = now
 
    upgrade_hint = {
        "free":       "upgrade ke Pro (50 analisis/hari)",
        "pro":        "upgrade ke Enterprise (500 analisis/hari)",
        "enterprise": "hubungi support untuk menaikkan limit",
    }
 
    # --- Lapis 1: cek limit analisis ---
    if quota.daily_used < quota.daily_limit:
        # Normal: masih ada jatah analisis
        quota.daily_used    += 1
        quota.total_analyses += 1
        await db.commit()
        return  # ✅ lanjut ke proses analisis
 
    # --- Lapis 2: analisis habis, cek token budget ---
    # Ambil token_daily_limit — pakai kolom kalau sudah ada, fallback ke konstanta per-plan
    token_daily_limit = getattr(quota, "token_daily_limit", None)
    if token_daily_limit is None:
        # Fallback: kalau kolom belum ada, pakai nilai per-plan
        _TOKEN_PLAN_LIMITS = {
            "free":       50_000,
            "pro":        500_000,
            "enterprise": 10_000_000,
        }
        plan_str = getattr(user.plan, "value", user.plan)
        token_daily_limit = _TOKEN_PLAN_LIMITS.get(plan_str, 50_000)
 
    token_used      = quota.total_tokens_used  # total kumulatif (belum ada daily token reset)
    token_remaining = max(0, token_daily_limit - token_used)
 
    if token_remaining >= TOKEN_COST_PER_ANALYSIS:
        # Token masih cukup untuk satu analisis lagi
        # TIDAK increment daily_used (sudah lewat limit), tapi catat di total_analyses
        quota.total_analyses += 1
        # Token aktual baru dikurangi setelah analisis selesai (di caller),
        # tapi kita commit dulu supaya data konsisten
        await db.commit()
        return  # ✅ lanjut ke proses analisis via token budget
 
    # --- Kedua limit habis ---
    plan_str = getattr(user.plan, "value", user.plan)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "code":    "QUOTA_EXHAUSTED",
            "message": (
                f"Kuota harian habis: {quota.daily_limit} analisis telah digunakan "
                f"dan sisa token ({token_remaining:,}) tidak cukup untuk satu analisis lagi "
                f"(butuh minimal {TOKEN_COST_PER_ANALYSIS:,} token). "
                f"Silakan {upgrade_hint.get(plan_str, 'hubungi support')}."
            ),
            "daily_used":        quota.daily_used,
            "daily_limit":       quota.daily_limit,
            "token_used":        token_used,
            "token_daily_limit": token_daily_limit,
            "token_remaining":   token_remaining,
        },
    )


# ─────────────────────────────────────────────
# Serializers
# ─────────────────────────────────────────────

def serialize_document(doc: Document) -> dict:
    return {
        "id": str(doc.id), # PERBAIKAN: Cast ke string
        "filename": doc.original_filename,
        "file_size": doc.file_size_bytes,
        "file_size_mb": doc.file_size_mb,
        "page_count": doc.page_count,
        "word_count": doc.word_count,
        "language": doc.language,
        "title": doc.title,
        "author": doc.author,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
    }


def serialize_analysis(analysis: AnalysisResult) -> dict:
    return {
        "id": str(analysis.id), # PERBAIKAN: Cast ke string
        "document_id": str(analysis.document_id) if analysis.document_id else None,
        "analysis_type": analysis.analysis_type,
        "result": analysis.result,
        "key_points": analysis.key_points,
        "recommendations": analysis.recommendations,
        "provider": analysis.provider,
        "model_used": analysis.model_used,
        "tokens_used": analysis.tokens_used,
        "processing_time_ms": analysis.processing_time_ms,
        "is_successful": analysis.is_successful,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


def serialize_chat(chat: ChatHistory) -> dict:
    return {
        "id": str(chat.id), # PERBAIKAN: Cast ke string
        "session_id": str(chat.session_id) if chat.session_id else None,
        "session_title": chat.session_title,
        "role": chat.role,
        "content": chat.content,
        "provider": chat.provider,
        "model_used": chat.model_used,
        "tokens_used": chat.tokens_used,
        "processing_time_ms": chat.processing_time_ms,
        "feedback": chat.feedback,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
    }


# ─────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────

# @router.post("/upload", status_code=status.HTTP_201_CREATED)
# async def upload_document(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     if not file.filename or not file.filename.lower().endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Hanya file PDF yang diperbolehkan.")

#     content = await file.read()

#     try:
#         file_info = await pdf_extractor.save_uploaded_file(content, file.filename)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     doc = Document(user_id=current_user.id, status="processing", **file_info)
#     db.add(doc)
#     await db.commit()
#     await db.refresh(doc)

#     extraction = await asyncio.get_event_loop().run_in_executor(
#         None, pdf_extractor.extract, file_info["file_path"]
#     )

#     if extraction.success:
#         doc.status = "completed"
#         doc.extracted_text = extraction.text
#         doc.page_count = extraction.page_count
#         doc.word_count = extraction.word_count
#         doc.language = extraction.language
#         doc.title = extraction.title
#         doc.author = extraction.author
#         doc.subject = extraction.subject
#         doc.processed_at = datetime.now(timezone.utc)
#     else:
#         doc.status = "failed"
#         doc.error_message = extraction.error

#     await db.commit()
#     await db.refresh(doc)

#     quota = await get_user_quota(current_user, db)
#     quota.storage_used_bytes += file_info["file_size_bytes"]
#     quota.total_documents += 1
#     quota.total_pages_processed += extraction.page_count or 0
#     await db.commit()

#     return {
#         "message": "Dokumen berhasil diupload dan diproses.",
#         "document": serialize_document(doc),
#         "extraction": {
#             "success": extraction.success,
#             "preview": pdf_extractor.get_text_preview(extraction.text, 300),
#             "error": extraction.error,
#         },
#     }
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Validasi ekstensi — delegasi ke extractor (sudah handle semua format)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nama file tidak valid.")
 
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        from app.services.document_extractor import SUPPORTED_EXTENSIONS as SE
        supported = ", ".join(sorted(SE.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Format '{ext}' tidak didukung. Format yang didukung: {supported}",
        )
 
    content = await file.read()
 
    try:
        file_info = await document_extractor.save_uploaded_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
 
    doc = Document(user_id=current_user.id, status="processing", **file_info)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
 
    # Ekstraksi di thread pool (blocking I/O)
    extraction = await asyncio.get_event_loop().run_in_executor(
        None, document_extractor.extract, file_info["file_path"]
    )
 
    if extraction.success:
        doc.status         = "completed"
        doc.extracted_text = extraction.text
        doc.page_count     = extraction.page_count
        doc.word_count     = extraction.word_count
        doc.language       = extraction.language
        doc.title          = extraction.title
        doc.author         = extraction.author
        doc.subject        = extraction.subject
        doc.processed_at   = datetime.now(timezone.utc)
    else:
        doc.status        = "failed"
        doc.error_message = extraction.error
 
    await db.commit()
    await db.refresh(doc)
 
    quota = await get_user_quota(current_user, db)
    quota.storage_used_bytes    += file_info["file_size_bytes"]
    quota.total_documents        += 1
    quota.total_pages_processed  += extraction.page_count or 0
    await db.commit()
 
    return {
        "message": "Dokumen berhasil diupload dan diproses.",
        "document": serialize_document(doc),
        "extraction": {
            "success":   extraction.success,
            "file_type": extraction.file_type,
            "preview":   document_extractor.get_text_preview(extraction.text, 300),
            "error":     extraction.error,
        },
    }


# ─────────────────────────────────────────────
# Analyze
# ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_document(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc_result = await db.execute(
        select(Document).where(
            and_(Document.id == payload.document_id, Document.user_id == current_user.id)
        )
    )
    doc = doc_result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")
    if doc.status != "completed":
        raise HTTPException(status_code=400, detail=f"Dokumen belum siap (status: {doc.status}).")
    if not doc.extracted_text:
        raise HTTPException(status_code=400, detail="Teks dokumen kosong.")

    quota = await get_user_quota(current_user, db)
    await check_and_consume_quota(current_user, quota, db)

    mode_map = {
        "summary": AnalysisMode.SUMMARY,
        "key_points": AnalysisMode.KEY_POINTS,
        "recommendations": AnalysisMode.RECOMMENDATIONS,
        "custom": AnalysisMode.CUSTOM,
    }
    mode = mode_map.get(payload.analysis_type, AnalysisMode.SUMMARY)

    type_map = {
        "summary": "summary",
        "key_points": "extraction",
        "recommendations": "comparison",
        "custom": "custom",
    }

    ai_result = await ai_orchestrator.analyze(
        text=doc.extracted_text,
        mode=mode,
        custom_prompt=payload.custom_prompt,
        max_tokens=2048,
    )

    analysis = AnalysisResult(
        user_id=current_user.id,
        document_id=doc.id,
        analysis_type=type_map.get(payload.analysis_type, "summary"),
        prompt=payload.custom_prompt,
        result=ai_result.get("content"),
        provider=ai_result.get("provider", "fallback"),
        model_used=ai_result.get("model"),
        tokens_used=ai_result.get("tokens_used", 0),
        processing_time_ms=ai_result.get("processing_time_ms", 0),
        is_successful=ai_result.get("success", False),
        error_message=ai_result.get("error"),
    )
    db.add(analysis)
    quota.total_tokens_used += ai_result.get("tokens_used", 0)
    await db.commit()
    await db.refresh(analysis)

    return {
        "message": "Analisis selesai." if ai_result.get("success") else "Analisis gagal.",
        "analysis": serialize_analysis(analysis),
        "quota": {
            "daily_used": quota.daily_used,
            "daily_remaining": quota.daily_remaining,
        },
    }


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

@router.post("/chat")
async def chat_with_document(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc_result = await db.execute(
        select(Document).where(
            and_(Document.id == payload.document_id, Document.user_id == current_user.id)
        )
    )
    doc = doc_result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")
    if doc.status != "completed":
        raise HTTPException(status_code=400, detail=f"Dokumen belum siap (status: {doc.status}).")
    if not doc.extracted_text:
        raise HTTPException(status_code=400, detail="Dokumen belum diproses.")

    quota = await get_user_quota(current_user, db)
    await check_and_consume_quota(current_user, quota, db)

    session_id = payload.session_id or str(uuid.uuid4())

    history_result = await db.execute(
        select(ChatHistory)
        .where(
            and_(
                ChatHistory.session_id == session_id,
                ChatHistory.document_id == payload.document_id,
                ChatHistory.user_id == current_user.id,
            )
        )
        .order_by(ChatHistory.created_at)
        .limit(12)
    )
    history = history_result.scalars().all()
    history_list = [{"role": h.role, "content": h.content} for h in history]

    is_first_message = len(history) == 0
    session_title = payload.message[:80] if is_first_message else None

    user_msg = ChatHistory(
        user_id=current_user.id,
        document_id=doc.id,
        session_id=session_id,
        session_title=session_title,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    await db.flush()

    ai_result = await ai_orchestrator.chat(
        document_text=doc.extracted_text,
        user_message=payload.message,
        chat_history=history_list,
        max_tokens=1024,
    )

    assistant_msg = ChatHistory(
        user_id=current_user.id,
        document_id=doc.id,
        session_id=session_id,
        session_title=None,
        role="assistant",
        content=ai_result.get("content") or ai_result.get("error") or "Maaf, terjadi kesalahan.",
        provider=ai_result.get("provider", "fallback"),
        model_used=ai_result.get("model"),
        tokens_used=ai_result.get("tokens_used", 0),
        processing_time_ms=ai_result.get("processing_time_ms", 0),
    )
    db.add(assistant_msg)
    quota.total_tokens_used += ai_result.get("tokens_used", 0)
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    return {
        "session_id": session_id,
        "is_new_session": is_first_message,
        "user_message": serialize_chat(user_msg),
        "assistant_message": serialize_chat(assistant_msg),
        "success": ai_result.get("success", False),
        "quota": {
            "daily_used": quota.daily_used,
            "daily_remaining": quota.daily_remaining,
        },
    }


@router.put("/chat/{chat_id}/feedback")
async def update_chat_feedback(
    chat_id: str,
    payload: ChatFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.feedback not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="Feedback harus 'like' atau 'dislike'.")

    result = await db.execute(
        select(ChatHistory).where(
            and_(ChatHistory.id == chat_id, ChatHistory.user_id == current_user.id)
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Pesan tidak ditemukan.")

    chat.feedback = payload.feedback
    await db.commit()
    return {"message": "Feedback berhasil disimpan."}


# ─────────────────────────────────────────────
# List Documents
# ─────────────────────────────────────────────

@router.get("/")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count(Document.id)).where(
            and_(Document.user_id == current_user.id, Document.deleted_at.is_(None))
        )
    )
    total = total_result.scalar_one() or 0

    docs_result = await db.execute(
        select(Document)
        .where(and_(Document.user_id == current_user.id, Document.deleted_at.is_(None)))
        .order_by(desc(Document.created_at))
        .offset(offset)
        .limit(page_size)
    )
    docs = docs_result.scalars().all()

    return {
        "documents": [serialize_document(d) for d in docs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        },
    }


# ─────────────────────────────────────────────
# History
# ─────────────────────────────────────────────

@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    analysis_query = (
        select(AnalysisResult, Document.original_filename)
        .join(Document, AnalysisResult.document_id == Document.id)
        .where(AnalysisResult.user_id == current_user.id)
    )
    if document_id:
        analysis_query = analysis_query.where(AnalysisResult.document_id == document_id)
    analysis_query = analysis_query.order_by(desc(AnalysisResult.created_at)).limit(page_size)
    analysis_result = await db.execute(analysis_query)
    analyses = analysis_result.all()

    chat_query = (
        select(
            ChatHistory.session_id,
            func.min(ChatHistory.session_title).label("session_title"),
            ChatHistory.document_id,
            func.min(Document.original_filename).label("original_filename"),
            func.count(ChatHistory.id).label("message_count"),
            func.max(ChatHistory.created_at).label("last_message_at"),
        )
        .join(Document, ChatHistory.document_id == Document.id, isouter=True)
        .where(and_(ChatHistory.user_id == current_user.id, ChatHistory.role == "user"))
        .group_by(ChatHistory.session_id, ChatHistory.document_id)
        .order_by(desc(func.max(ChatHistory.created_at)))
        .limit(page_size)
    )
    if document_id:
        chat_query = chat_query.where(ChatHistory.document_id == document_id)
    chat_result = await db.execute(chat_query)
    chat_sessions = chat_result.all()

    # PERBAIKAN: Pastikan session_id dan document_id diserialisasi dengan benar ke string
    return {
        "analyses": [
            {**serialize_analysis(a[0]), "document_filename": a[1]}
            for a in analyses
        ],
        "chat_sessions": [
            {
                "session_id": str(s.session_id) if s.session_id else None,
                "session_title": s.session_title or "Sesi Chat",
                "document_id": str(s.document_id) if s.document_id else None,
                "document_filename": s.original_filename,
                "message_count": s.message_count,
                "last_message_at": (
                    s.last_message_at.isoformat() if s.last_message_at else None
                ),
            }
            for s in chat_sessions
        ],
    }


@router.get("/chat/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatHistory)
        .where(
            and_(
                ChatHistory.session_id == session_id,
                ChatHistory.user_id == current_user.id,
            )
        )
        .order_by(ChatHistory.created_at)
    )
    messages = result.scalars().all()
    return {
        "session_id": session_id,
        "messages": [serialize_chat(m) for m in messages],
        "count": len(messages),
    }


# ─────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    quota = await get_user_quota(current_user, db)

    doc_result = await db.execute(
        select(func.count(Document.id)).where(
            and_(Document.user_id == current_user.id, Document.deleted_at.is_(None))
        )
    )
    total_docs = doc_result.scalar_one() or 0

    analysis_counts = await db.execute(
        select(AnalysisResult.analysis_type, func.count(AnalysisResult.id))
        .where(AnalysisResult.user_id == current_user.id)
        .group_by(AnalysisResult.analysis_type)
    )
    analysis_by_type = {row[0]: row[1] for row in analysis_counts.all()}

    provider_counts = await db.execute(
        select(AnalysisResult.provider, func.count(AnalysisResult.id))
        .where(AnalysisResult.user_id == current_user.id)
        .group_by(AnalysisResult.provider)
    )
    analysis_by_provider = {row[0]: row[1] for row in provider_counts.all()}

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count(AnalysisResult.id)).where(
            and_(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.created_at >= seven_days_ago,
            )
        )
    )
    recent_count = recent_result.scalar_one() or 0

    return {
        "user": {
            "id": str(current_user.id), # PERBAIKAN: Pastikan ini string
            "plan": current_user.plan,
            "username": current_user.username,
        },
        "quota": {
            "daily_used": quota.daily_used,
            "daily_limit": quota.daily_limit,
            "daily_remaining": quota.daily_remaining,
            "usage_percentage": quota.usage_percentage,
            "total_analyses": quota.total_analyses,
            "total_documents": quota.total_documents,
            "total_pages_processed": quota.total_pages_processed,
            "total_tokens_used": quota.total_tokens_used,
            "storage_used_mb": quota.storage_used_mb,
        },
        "documents": {"total": total_docs},
        "analyses": {
            "total": quota.total_analyses,
            "by_type": analysis_by_type,
            "by_provider": analysis_by_provider,
            "last_7_days": recent_count,
        },
        "ai_providers": ai_orchestrator.get_provider_status(),
    }


# ─────────────────────────────────────────────
# Single Document & Delete
# ─────────────────────────────────────────────

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    include_analyses: bool = Query(True),   # default True agar AnalysisView langsung dapat data
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")

    data = {"document": serialize_document(doc)}

    if include_analyses:
        analyses_result = await db.execute(
            select(AnalysisResult)
            .where(AnalysisResult.document_id == document_id)
            .order_by(desc(AnalysisResult.created_at))
            .limit(20)
        )
        data["analyses"] = [serialize_analysis(a) for a in analyses_result.scalars().all()]

    return data


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")

    # Hapus file fisik dari disk
    # await pdf_extractor.delete_file(doc.file_path)
    await document_extractor.delete_file(doc.file_path)

    doc.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    quota = await get_user_quota(current_user, db)
    quota.storage_used_bytes = max(0, quota.storage_used_bytes - doc.file_size_bytes)
    await db.commit()

    return {"message": "Dokumen berhasil dihapus."}