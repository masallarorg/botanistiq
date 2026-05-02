import os
import base64
import binascii
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials
except Exception:  # Firebase verification is optional in local dev.
    firebase_admin = None
    firebase_auth = None
    credentials = None


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("BOTANISTIQ_OPENAI_MODEL", "gpt-4o-mini").strip()
ALLOWED_ORIGINS_RAW = os.environ.get("BOTANISTIQ_ALLOWED_ORIGINS", "*").strip()
ALLOWED_ORIGINS = [item.strip() for item in ALLOWED_ORIGINS_RAW.split(",") if item.strip()] or ["*"]

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(
    title="Botanistiq API",
    version="1.0.0",
    description="Plant-only live photo chat backend for Botanistiq.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str


class ChatPhoto(BaseModel):
    name: str = "plant.jpg"
    mimeType: str = "image/jpeg"
    base64: str


class PlantLivePhotoChatRequest(BaseModel):
    locale: str = "tr"
    mode: str = "only_selected_plant_or_uploaded_photos"
    premium: bool = False
    scopeId: str
    scopeLabel: str
    plant: dict[str, Any] | None = None
    photos: list[ChatPhoto] = Field(default_factory=list)
    question: str
    history: list[ChatMessage] = Field(default_factory=list)
    guardrails: dict[str, Any] = Field(default_factory=dict)
    system_instruction: str | None = None


class PlantAnalyzeRequest(BaseModel):
    locale: str = "tr"
    photos: list[ChatPhoto] = Field(default_factory=list)
    hint: str | None = None


def init_firebase_if_available() -> None:
    if firebase_admin is None:
        return
    if firebase_admin._apps:
        return

    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    try:
        if credentials_path and os.path.exists(credentials_path):
            firebase_admin.initialize_app(credentials.Certificate(credentials_path))
        else:
            # Works automatically on Google Cloud if service account is attached.
            firebase_admin.initialize_app()
    except Exception:
        # Local backend should still run without Firebase Admin.
        pass


init_firebase_if_available()


async def verify_optional_firebase_token(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    if firebase_auth is None or firebase_admin is None or not firebase_admin._apps:
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        return firebase_auth.verify_id_token(token)
    except Exception:
        return None


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "botanistiq-api",
        "openaiConfigured": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
        "firebaseAdminConfigured": bool(firebase_admin and firebase_admin._apps),
    }


def is_off_topic(question: str) -> bool:
    q = question.lower()
    blocked = [
        "bitcoin", "kripto", "crypto", "borsa", "hisse", "futbol", "maç", "mac",
        "siyaset", "seçim", "secim", "kod", "flutter", "python", "hava durumu",
        "film", "dizi", "aşk", "ask", "iliski", "ilişki", "yemek tarifi",
        "araba", "oyun", "şarkı", "sarki",
    ]
    return any(item in q for item in blocked)


def validate_photos(photos: list[ChatPhoto], max_count: int) -> list[ChatPhoto]:
    clean = photos[:max_count]
    for photo in clean:
        if not photo.base64:
            raise HTTPException(status_code=422, detail="Photo base64 is empty.")
        try:
            # Validate only; don't keep decoded bytes in memory.
            base64.b64decode(photo.base64[:1024] + "==", validate=False)
        except (binascii.Error, ValueError):
            raise HTTPException(status_code=422, detail=f"Invalid base64 photo: {photo.name}")
        if not photo.mimeType.startswith("image/"):
            raise HTTPException(status_code=422, detail=f"Invalid image mime type: {photo.mimeType}")
    return clean


def refusal(locale: str) -> dict[str, Any]:
    if locale == "tr":
        return {
            "offTopic": True,
            "answer": (
                "Bu sohbet sadece seçili bitki veya eklenen fotoğraflar hakkındadır. "
                "Bu bitkinin yaprakları, toprak, sulama, ışık, hastalık belirtisi veya kurtarma adımı hakkında sor."
            ),
        }
    return {
        "offTopic": True,
        "answer": "This chat is only about the selected plant or added photos. Ask about this plant’s leaves, soil, watering, light, symptoms, or rescue steps.",
    }


def plant_context_text(payload: PlantLivePhotoChatRequest) -> str:
    plant = payload.plant or {}
    return f"""
Selected scope: {payload.scopeLabel}
Saved plant analysis:
- Name: {plant.get("name", payload.scopeLabel)}
- Health score: {plant.get("health_score", "unknown")}
- Severity: {plant.get("severity", "unknown")}
- Diagnosis summary: {plant.get("diagnosis_summary", "")}
- Likely causes: {plant.get("likely_causes", [])}
- Immediate actions: {plant.get("immediate_actions", [])}
- Avoid actions: {plant.get("avoid_actions", [])}
- 7-day rescue plan: {plant.get("rescue_plan_7_days", [])}
- Watering: {plant.get("watering_tip", "")}
- Soil: {plant.get("soil_tip", "")}
- Light: {plant.get("light_advice", "")}
- Placement: {plant.get("placement_advice", "")}
- Room / placement: {plant.get("room", "")} / {plant.get("placement", "")}
- Confidence: {plant.get("confidence_label", "")}
- Scan quality: {plant.get("scan_quality_summary", "")}
Uploaded photo count: {len(payload.photos)}
"""


def build_system(locale: str) -> str:
    if locale == "tr":
        return (
            "Sen Botanistiq uygulamasında çalışan bitki fotoğrafı asistanısın. "
            "Sadece seçili kayıtlı bitki veya bu oturumda yüklenen fotoğraflar hakkında cevap ver. "
            "Başka konu, başka bitki, kod, finans, siyaset, hava durumu ve genel sohbet istenirse kibarca reddet. "
            "Önceki cevabı aynen tekrarlama. Son soruya özel cevap ver. "
            "Görselden emin olmadığın bulguyu kesin hastalık gibi söyleme. "
            "Kısa, net, uygulanabilir ve mümkünse 'bugün yapılacak' adımları ver."
        )
    return (
        "You are the plant-photo assistant inside Botanistiq. "
        "Answer only about the selected saved plant or the photos uploaded in this session. "
        "Politely refuse unrelated topics, other plants, code, finance, politics, weather, and general chat. "
        "Do not repeat the previous answer verbatim. Address the latest question specifically. "
        "Do not state uncertain visual findings as certain disease diagnoses. "
        "Keep answers short, clear, actionable, and include what to do today when possible."
    )


def photo_to_openai_image(photo: ChatPhoto) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{photo.mimeType};base64,{photo.base64}",
            "detail": "low",
        },
    }


@app.post("/api/v1/plant-live-photo-chat")
async def plant_live_photo_chat(
    payload: PlantLivePhotoChatRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if not OPENAI_API_KEY or client is None:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on backend.")

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question is empty.")

    if is_off_topic(question):
        return refusal(payload.locale)

    if not payload.photos and not payload.plant:
        raise HTTPException(status_code=422, detail="A saved plant context or at least one photo is required.")

    decoded_token = await verify_optional_firebase_token(authorization)
    max_photos = 4 if payload.premium else 1
    clean_photos = validate_photos(payload.photos, max_photos)

    system = payload.system_instruction or build_system(payload.locale)
    context = plant_context_text(payload)

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"{system}\n\n"
                f"{context}\n\n"
                f"User question: {question}\n\n"
                "Important: answer only using the selected plant context and uploaded photos. "
                "Do not answer unrelated questions."
            ),
        }
    ]

    for photo in clean_photos:
        content.append(photo_to_openai_image(photo))

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
    ]

    for item in payload.history[-8:]:
        if item.role in ("user", "assistant") and item.text.strip():
            messages.append({"role": item.role, "content": item.text[:900]})

    messages.append({"role": "user", "content": content})

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.35,
            max_tokens=500,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc

    answer = completion.choices[0].message.content or ""
    answer = answer.strip()
    if not answer:
        raise HTTPException(status_code=502, detail="AI provider returned empty answer.")

    return {
        "answer": answer,
        "scopeId": payload.scopeId,
        "scopeLabel": payload.scopeLabel,
        "photoCount": len(clean_photos),
        "premium": payload.premium,
        "verifiedUser": bool(decoded_token),
    }


@app.post("/api/v1/analyze-plant")
async def analyze_plant(payload: PlantAnalyzeRequest) -> dict[str, Any]:
    """Optional simple photo analysis endpoint.

    Mobil uygulamanın mevcut tarama endpointi farklıysa bunu kullanmak zorunda değilsin.
    Bu endpoint backend'in içinde hazır dursun diye eklendi.
    """
    if not OPENAI_API_KEY or client is None:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on backend.")

    clean_photos = validate_photos(payload.photos, 5)
    if not clean_photos:
        raise HTTPException(status_code=422, detail="At least one photo is required.")

    system = (
        "You are Botanistiq plant analysis backend. Return concise JSON-like Turkish output. "
        "Analyze only the plant in the uploaded photos. Do not discuss unrelated topics."
    )

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Fotoğraftaki bitkiyi analiz et. Şu alanları kısa cevapla: "
                "muhtemel bitki adı, sağlık skoru 0-100, kesin/olası sorun, sulama, toprak, ışık, bugün yapılacaklar, 7 günlük kurtarma planı. "
                f"Kullanıcı ipucu: {payload.hint or ''}"
            ),
        }
    ]
    for photo in clean_photos:
        content.append(photo_to_openai_image(photo))

    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        temperature=0.25,
        max_tokens=700,
    )

    return {"analysis": (completion.choices[0].message.content or "").strip()}

# MOUNTED_ASSET_ROUTES_V44
# The user's existing backend package under backend/app is mounted here.
# If optional dependencies/settings are not ready, the core live-chat endpoint remains active.
try:
    from app.api.routes import router as mounted_plant_ai_router
    app.include_router(mounted_plant_ai_router)
except Exception as exc:  # noqa: BLE001
    @app.get('/api/v1/mounted-backend-status')
    async def mounted_backend_status() -> dict[str, str]:
        return {
            'status': 'not_mounted',
            'reason': str(exc),
            'hint': 'Check backend/.env OPENAI_API_KEY and requirements installation.',
        }

