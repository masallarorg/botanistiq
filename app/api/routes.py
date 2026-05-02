from fastapi import APIRouter, HTTPException
import traceback
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, BadRequestError

from app.models.contracts import DiagnoseRequest, PlantScreenResponse, ScanAnalyzeResponse, PlantLivePhotoChatRequest, PlantLivePhotoChatResponse
from app.services.openai_service import OpenAIPlantService

router = APIRouter(prefix="/api/v1", tags=["plant-ai"])
service = OpenAIPlantService()

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def _translate_exc(exc: Exception, context: str = "AI") -> HTTPException:
    print(f"BOTANISTIQ_BACKEND_ERROR[{context}]: {type(exc).__name__}: {exc}", flush=True)
    traceback.print_exc()
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=500, detail="OPENAI_AUTH_INVALID")
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return HTTPException(status_code=503, detail="OPENAI_UNREACHABLE")
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=429, detail="OPENAI_RATE_LIMIT")
    if isinstance(exc, BadRequestError):
        return HTTPException(status_code=500, detail=f"OPENAI_BAD_REQUEST:{exc}")
    return HTTPException(status_code=500, detail=f"{context}_FAILED:{type(exc).__name__}:{exc}")

@router.post("/screen-plant", response_model=PlantScreenResponse)
def screen_plant(payload: DiagnoseRequest) -> PlantScreenResponse:
    try:
        return service.screen_for_plant(payload.image_url, payload.locale, payload.notes)
    except Exception as exc:  # noqa: BLE001
        raise _translate_exc(exc, context='SCAN_ANALYZE') from exc

@router.post("/scan-analyze", response_model=ScanAnalyzeResponse)
def scan_analyze(payload: DiagnoseRequest) -> ScanAnalyzeResponse:
    try:
        screening = service.screen_for_plant(payload.image_url, payload.locale, payload.notes)
        if not screening.is_plant:
            return ScanAnalyzeResponse(is_plant=False, reject_reason=screening.reason)

        identify_result = service.identify(payload.image_url, payload.locale, payload.notes)
        diagnose_result = service.diagnose(
            payload.image_url,
            payload.locale,
            payload.plant_name or identify_result.common_name,
            payload.notes,
        )
        care_plan_result = service.care_plan(
            payload.locale,
            payload.plant_name or identify_result.common_name,
            diagnose_result.diagnosis_summary,
            diagnose_result.health_score,
            payload.notes,
        )
        plant_parent_result = service.plant_parent_profile(
            payload.locale,
            payload.plant_name or identify_result.common_name,
            diagnose_result.diagnosis_summary,
            payload.notes,
        )
        return ScanAnalyzeResponse(
            is_plant=True,
            identify=identify_result,
            diagnose=diagnose_result,
            care_plan=care_plan_result,
            plant_parent=plant_parent_result,
        )
    except Exception as exc:  # noqa: BLE001
        raise _translate_exc(exc, context='SCAN_ANALYZE') from exc


@router.post("/plant-live-photo-chat", response_model=PlantLivePhotoChatResponse)
def plant_live_photo_chat(payload: PlantLivePhotoChatRequest) -> PlantLivePhotoChatResponse:
    try:
        q = (payload.question or "").lower()
        off_topic_words = [
            "bitcoin", "kripto", "crypto", "borsa", "hisse", "futbol", "maç", "mac",
            "siyaset", "seçim", "secim", "kod", "flutter", "python", "hava durumu",
            "film", "dizi", "aşk", "ask", "ilişki", "iliski", "yemek tarifi",
        ]
        if any(word in q for word in off_topic_words):
            answer = (
                "Bu sohbet sadece seçili bitki veya eklediğin fotoğraflar hakkındadır. "
                "Bu bitkinin yaprakları, toprak, sulama, ışık, hastalık belirtisi veya kurtarma adımı hakkında sor."
                if payload.locale == "tr"
                else "This chat is only about the selected plant or added photos. Ask about this plant's leaves, soil, watering, light, symptoms, or rescue steps."
            )
            return PlantLivePhotoChatResponse(answer=answer, offTopic=True)

        return PlantLivePhotoChatResponse(answer=service.live_photo_chat(payload), offTopic=False)
    except Exception as exc:  # noqa: BLE001
        raise _translate_exc(exc, context='LIVE_CHAT') from exc
