import json
from typing import Any
from openai import OpenAI
from app.core.settings import settings
from app.models.contracts import (
    CarePlanResponse, DiagnoseResponse, IdentifyResponse,
    PlantParentProfileResponse, PlantScreenResponse,
)

class OpenAIPlantService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def _responses_json(self, instruction: str, user_text: str, image_url: str | None = None) -> dict[str, Any]:
        content = [{"type": "input_text", "text": user_text}]
        if image_url:
            content.append({"type": "input_image", "image_url": image_url})

        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": content}],
            instructions=instruction,
            temperature=0.2,
        )
        text = getattr(response, "output_text", None)
        if not text:
            raise ValueError("OpenAI response did not include output_text.")
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start:end + 1])

    def screen_for_plant(self, image_url: str, locale: str = "tr", notes: str | None = None) -> PlantScreenResponse:
        instruction = 'Return only valid JSON: {"is_plant": boolean, "reason": string, "subject_hint": string|null}.'
        user_text = f"Language: {locale}. User notes: {notes or 'none'}. Determine whether the image is plant-related."
        return PlantScreenResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def identify(self, image_url: str, locale: str = "tr", notes: str | None = None) -> IdentifyResponse:
        instruction = 'Return only valid JSON: {"common_name": string, "scientific_name": string, "confidence": integer 0-100, "short_description": string}.'
        user_text = f"Language: {locale}. User notes: {notes or 'none'}. Identify the plant."
        return IdentifyResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def diagnose(self, image_url: str, locale: str = "tr", plant_name: str | None = None, notes: str | None = None) -> DiagnoseResponse:
        instruction = 'Return only valid JSON: {"health_score": integer 0-100, "severity": "low"|"medium"|"high"|"critical", "diagnosis_summary": string, "likely_causes": [{"title": string, "confidence": integer 0-100, "explanation": string}], "immediate_actions": [string], "avoid_actions": [string]}.'
        user_text = f"Language: {locale}. Plant hint: {plant_name or 'unknown'}. User notes: {notes or 'none'}. Diagnose the plant."
        return DiagnoseResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def care_plan(self, locale: str, plant_name: str, diagnosis_summary: str, health_score: int, notes: str | None = None) -> CarePlanResponse:
        instruction = 'Return only valid JSON: {"today": [{"title": string, "details": string}], "this_week": [{"title": string, "details": string}], "next_check_in_days": integer, "long_term_tips": [string]}.'
        user_text = f"Language: {locale}. Plant: {plant_name}. Health score: {health_score}. Diagnosis: {diagnosis_summary}. Notes: {notes or 'none'}. Create a care plan."
        return CarePlanResponse.model_validate(self._responses_json(instruction, user_text))

    def plant_parent_profile(self, locale: str, plant_name: str, diagnosis_summary: str, notes: str | None = None) -> PlantParentProfileResponse:
        instruction = 'Return only valid JSON: {"placement": "indoor"|"balcony"|"garden"|"mixed", "placement_advice": string, "pet_safety": string, "child_safety": string, "vacation_tip": string, "soil_tip": string, "watering_tip": string, "watering_interval_days": integer, "soil_change_interval_days": integer}.'
        user_text = f"Language: {locale}. Plant: {plant_name}. Diagnosis: {diagnosis_summary}. Notes: {notes or 'none'}. Create home care guidance."
        return PlantParentProfileResponse.model_validate(self._responses_json(instruction, user_text))
