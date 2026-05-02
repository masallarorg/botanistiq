from typing import Literal
from pydantic import BaseModel, Field

class DiagnoseRequest(BaseModel):
    image_url: str
    locale: Literal["tr", "en"] = "tr"
    notes: str | None = None
    plant_name: str | None = None

class IdentifyResponse(BaseModel):
    common_name: str
    scientific_name: str
    confidence: int = Field(..., ge=0, le=100)
    short_description: str

class DiagnoseCause(BaseModel):
    title: str
    confidence: int = Field(..., ge=0, le=100)
    explanation: str

class DiagnoseResponse(BaseModel):
    health_score: int = Field(..., ge=0, le=100)
    severity: Literal["low", "medium", "high", "critical"]
    diagnosis_summary: str
    likely_causes: list[DiagnoseCause]
    immediate_actions: list[str]
    avoid_actions: list[str]

class CareTask(BaseModel):
    title: str
    details: str

class CarePlanResponse(BaseModel):
    today: list[CareTask]
    this_week: list[CareTask]
    next_check_in_days: int
    long_term_tips: list[str]

class PlantParentProfileResponse(BaseModel):
    placement: Literal["indoor", "balcony", "garden", "mixed"]
    placement_advice: str
    pet_safety: str
    child_safety: str
    vacation_tip: str
    soil_tip: str
    watering_tip: str
    watering_interval_days: int = Field(..., ge=1, le=60)
    soil_change_interval_days: int = Field(..., ge=14, le=730)

class PlantScreenResponse(BaseModel):
    is_plant: bool
    reason: str
    subject_hint: str | None = None

class ScanAnalyzeResponse(BaseModel):
    is_plant: bool
    reject_reason: str | None = None
    identify: IdentifyResponse | None = None
    diagnose: DiagnoseResponse | None = None
    care_plan: CarePlanResponse | None = None
    plant_parent: PlantParentProfileResponse | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str

class ChatPhoto(BaseModel):
    name: str = "plant.jpg"
    mimeType: str = "image/jpeg"
    base64: str

class PlantLivePhotoChatRequest(BaseModel):
    locale: Literal["tr", "en"] = "tr"
    mode: str = "only_selected_plant_or_uploaded_photos"
    premium: bool = False
    scopeId: str
    scopeLabel: str
    plant: dict | None = None
    photos: list[ChatPhoto] = Field(default_factory=list)
    question: str
    history: list[ChatMessage] = Field(default_factory=list)
    guardrails: dict = Field(default_factory=dict)
    system_instruction: str | None = None

class PlantLivePhotoChatResponse(BaseModel):
    answer: str
    offTopic: bool = False
