"""
AI Orchestrator Service
Routing strategy: Gemini (primary) -> Groq (fallback) -> Local/Error
Handles retry logic, token counting, and response normalization.
"""
import time
import logging
from typing import Optional
from enum import Enum

import httpx
from app.core.config import settings
from app.db.models import AIProvider

logger = logging.getLogger(__name__)


class AnalysisMode(str, Enum):
    SUMMARY = "summary"
    CHAT = "chat"
    KEY_POINTS = "key_points"
    RECOMMENDATIONS = "recommendations"
    CUSTOM = "custom"


# ─────────────────────────────────────────────
# Prompt Templates
# ─────────────────────────────────────────────

PROMPTS = {
    AnalysisMode.SUMMARY: """Kamu adalah analis dokumen profesional. Buat ringkasan komprehensif dari dokumen PDF berikut dalam Bahasa Indonesia.

Format output:
**📋 Ringkasan Utama**
[2-3 paragraf ringkasan]

**🎯 Poin-Poin Kunci**
- [poin 1]
- [poin 2]
- [dst...]

**💡 Kesimpulan**
[1 paragraf kesimpulan]

Dokumen:
{text}""",

    AnalysisMode.KEY_POINTS: """Ekstrak poin-poin penting dari dokumen berikut. Sajikan dalam format terstruktur, ringkas, dan mudah dipahami dalam Bahasa Indonesia.

**🔑 Poin-Poin Penting:**
1. [poin pertama - singkat dan jelas]
2. [poin kedua]
...

**📊 Data/Angka Penting:**
[jika ada data numerik penting]

Dokumen:
{text}""",

    AnalysisMode.RECOMMENDATIONS: """Berikan analisis mendalam dan rekomendasi berdasarkan dokumen berikut. Fokus pada insight yang actionable dalam Bahasa Indonesia.

**🔍 Analisis Situasi:**
[analisis kondisi saat ini dari dokumen]

**✅ Rekomendasi Utama:**
1. [rekomendasi 1 - spesifik dan dapat dilakukan]
2. [rekomendasi 2]
...

**⚠️ Risiko yang Perlu Diwaspadai:**
- [risiko/tantangan yang diidentifikasi]

**📈 Langkah Selanjutnya:**
[prioritas tindakan yang disarankan]

Dokumen:
{text}""",

    AnalysisMode.CHAT: """{system_context}Kamu adalah asisten AI yang membantu menjawab pertanyaan tentang dokumen PDF. Jawab pertanyaan user berdasarkan konteks dokumen yang diberikan. Jika informasi tidak ada dalam dokumen, katakan dengan jujur.

Konteks Dokumen:
{text}

Pertanyaan User: {user_question}

Jawab dengan jelas, akurat, dan dalam Bahasa Indonesia (kecuali user meminta bahasa lain):""",

    AnalysisMode.CUSTOM: "{custom_prompt}\n\nDokumen:\n{text}",
}


# ─────────────────────────────────────────────
# AI Provider Clients
# ─────────────────────────────────────────────

class GeminiClient:
    """Google Gemini API client."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, max_tokens: int = 2048) -> dict:
        if not self.available:
            raise ValueError("Gemini API key tidak dikonfigurasi")

        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        tokens = usage.get("totalTokenCount", 0)

        return {
            "content": content,
            "tokens_used": tokens,
            "provider": AIProvider.GEMINI,
            "model": self.model,
        }


class GroqClient:
    """Groq API client (OpenAI-compatible)."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, max_tokens: int = 2048) -> dict:
        if not self.available:
            raise ValueError("Groq API key tidak dikonfigurasi")

        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return {
            "content": content,
            "tokens_used": tokens,
            "provider": AIProvider.GROQ,
            "model": self.model,
        }


# ─────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────

class AIOrchestrator:
    """
    Routes AI requests through providers with automatic fallback:
    Gemini (primary) -> Groq (secondary) -> Error with helpful message
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.groq = GroqClient()

    def _build_prompt(
        self,
        mode: AnalysisMode,
        text: str,
        user_question: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        system_context: str = "",
    ) -> str:
        # CUSTOM: gunakan custom_prompt sebagai instruksi utama
        if mode == AnalysisMode.CUSTOM:
            instruction = custom_prompt or user_question or "Analisis dokumen berikut secara umum."
            return f"{instruction}\n\nDokumen:\n{text[:8000]}"

        # CHAT: butuh system_context dan user_question
        if mode == AnalysisMode.CHAT:
            ctx_prefix = f"Riwayat percakapan sebelumnya:\n{system_context}\n\n" if system_context else ""
            template = PROMPTS[AnalysisMode.CHAT]
            return template.format(
                system_context=ctx_prefix,
                text=text[:8000],
                user_question=user_question or "",
            )

        # Semua mode lain: SUMMARY, KEY_POINTS, RECOMMENDATIONS
        template = PROMPTS.get(mode, PROMPTS[AnalysisMode.SUMMARY])
        return template.format(text=text[:8000])

    async def _run_with_fallback(self, prompt: str, max_tokens: int, start_time: float) -> dict:
        """Coba Gemini → Groq → error. Dipakai oleh analyze() dan chat()."""
        result = None
        errors = []

        if self.gemini.available:
            try:
                logger.info("Trying Gemini API...")
                result = await self.gemini.generate(prompt, max_tokens)
                logger.info(f"Gemini success: {result['tokens_used']} tokens")
            except Exception as e:
                errors.append(f"Gemini error: {str(e)}")
                logger.warning(f"Gemini failed, trying Groq: {e}")

        if result is None and self.groq.available:
            try:
                logger.info("Trying Groq API...")
                result = await self.groq.generate(prompt, max_tokens)
                logger.info(f"Groq success: {result['tokens_used']} tokens")
            except Exception as e:
                errors.append(f"Groq error: {str(e)}")
                logger.warning(f"Groq also failed: {e}")

        if result is None:
            error_detail = " | ".join(errors) if errors else "Semua provider AI tidak tersedia"
            logger.error(f"All AI providers failed: {error_detail}")
            return {
                "content": None,
                "tokens_used": 0,
                "provider": AIProvider.FALLBACK,
                "model": None,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "success": False,
                "error": (
                    "Layanan AI sementara tidak tersedia. "
                    "Pastikan API key sudah dikonfigurasi dengan benar. "
                    f"Detail: {error_detail}"
                ),
            }

        result["processing_time_ms"] = int((time.time() - start_time) * 1000)
        result["success"] = True
        result["error"] = None
        return result

    async def analyze(
        self,
        text: str,
        mode: AnalysisMode = AnalysisMode.SUMMARY,
        user_question: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Run AI analysis with automatic provider fallback.
        Returns standardized result dict.
        """
        start_time = time.time()
        prompt = self._build_prompt(
            mode=mode,
            text=text,
            user_question=user_question,
            custom_prompt=custom_prompt,
        )
        return await self._run_with_fallback(prompt, max_tokens, start_time)

    async def chat(
        self,
        document_text: str,
        user_message: str,
        chat_history: Optional[list] = None,
        max_tokens: int = 1024,
    ) -> dict:
        """
        Handle a chat message about a document.
        Includes previous chat turns for context continuity.
        """
        start_time = time.time()

        # Bangun string riwayat percakapan
        history_context = ""
        if chat_history:
            history_lines = []
            for turn in chat_history[-6:]:
                role = "User" if turn["role"] == "user" else "Asisten"
                history_lines.append(f"{role}: {turn['content']}")
            history_context = "\n".join(history_lines)

        prompt = self._build_prompt(
            mode=AnalysisMode.CHAT,
            text=document_text,
            user_question=user_message,
            system_context=history_context,
        )
        return await self._run_with_fallback(prompt, max_tokens, start_time)

    def get_provider_status(self) -> dict:
        """Return current availability status of all providers."""
        return {
            "gemini": {
                "available": self.gemini.available,
                "model": self.gemini.model,
            },
            "groq": {
                "available": self.groq.available,
                "model": self.groq.model,
            },
            "any_available": self.gemini.available or self.groq.available,
        }


# Singleton instance
ai_orchestrator = AIOrchestrator()