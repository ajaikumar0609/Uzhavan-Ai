"""
Voice endpoints for UZHAVAN AI. LOCAL-ONLY (zero-paid-API / local-first policy).

POST /voice/stt  - speech-to-text (audio -> Tamil/English transcript)
POST /voice/tts  - text-to-speech

The Android app does speech recognition and Tamil speech output on the device
(speech_to_text / flutter_tts) and does not call these routes. They exist for
self-hosted use only:

STT: faster-whisper running on this machine (WHISPER_PROVIDER=local). No audio leaves it.
TTS: no self-hosted engine is installed, so /voice/tts answers 503 and the client
     must use on-device TTS.

Deliberately NOT supported (they transmit farmer speech/text to third parties and/or bill):
OpenAI Whisper API, Google Cloud TTS, gTTS (Google Translate TTS). Do not re-add them.
"""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["Voice"])

_WHISPER_PROVIDER = os.getenv("WHISPER_PROVIDER", "browser-only")  # "local" | "browser-only"


# ── STT ───────────────────────────────────────────────────────────────────────

class TranscriptResponse(BaseModel):
    transcript: str
    language: str
    confidence: float | None = None
    provider: str


@router.post("/stt", response_model=TranscriptResponse)
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file (webm, wav, mp3, m4a)"),
    language: str = "ta",  # "ta" for Tamil, "en" for English
) -> TranscriptResponse:
    """Transcribe audio with the local faster-whisper model. Nothing is sent off this machine."""
    audio_bytes = await file.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio file too small or empty")

    if _WHISPER_PROVIDER == "local":
        return await _stt_local_whisper(audio_bytes, language)

    raise HTTPException(
        status_code=503,
        detail=(
            "Server-side STT is not enabled. Use the device's speech recognition, "
            "or install faster-whisper and set WHISPER_PROVIDER=local (runs locally)."
        ),
    )


async def _stt_local_whisper(audio_bytes: bytes, language: str) -> TranscriptResponse:
    """faster-whisper local - no API key, no network, runs on CPU."""
    try:
        from faster_whisper import WhisperModel  # type: ignore[import]
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            model = WhisperModel("small", device="cpu", compute_type="int8")
            lang_code = "ta" if language.startswith("ta") else None
            segments, info = model.transcribe(tmp_path, language=lang_code, beam_size=5)
            transcript = " ".join(s.text for s in segments).strip()
        finally:
            os.unlink(tmp_path)
        return TranscriptResponse(
            transcript=transcript,
            language=info.language,
            provider="faster-whisper-local",
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="faster-whisper not installed. Run: pip install faster-whisper",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Local Whisper error: {exc}")


# ── TTS ───────────────────────────────────────────────────────────────────────

@router.post("/tts")
async def text_to_speech(
    text: str,
    language: str = "ta",
    slow: bool = False,
) -> Response:
    """No self-hosted TTS engine is installed. Never forwards text to a cloud TTS."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    raise HTTPException(
        status_code=503,
        detail=(
            "Server-side TTS is not available (no self-hosted engine installed). "
            "Use the device's on-device text-to-speech."
        ),
    )
