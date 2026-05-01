from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, BadRequestError

from app.models.contracts import DiagnoseRequest, PlantScreenResponse, ScanAnalyzeResponse
from app.services.openai_service import OpenAIPlantService

router = APIRouter(prefix="/api/v1", tags=["plant-ai"])
service = OpenAIPlantService()

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def _translate_exc(exc: Exception) -> HTTPException:
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=500, detail="OPENAI_AUTH_INVALID")
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return HTTPException(status_code=503, detail="OPENAI_UNREACHABLE")
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=429, detail="OPENAI_RATE_LIMIT")
    if isinstance(exc, BadRequestError):
        return HTTPException(status_code=500, detail=f"OPENAI_BAD_REQUEST:{exc}")
    return HTTPException(status_code=500, detail=f"SCAN_ANALYZE_FAILED:{exc}")

@router.post("/screen-plant", response_model=PlantScreenResponse)
def screen_plant(payload: DiagnoseRequest) -> PlantScreenResponse:
    try:
        return service.screen_for_plant(payload.image_url, payload.locale, payload.notes)
    except Exception as exc:  # noqa: BLE001
        raise _translate_exc(exc) from exc

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
        raise _translate_exc(exc) from exc
