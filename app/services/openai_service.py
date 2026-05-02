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
        user_text = f"Language: {locale}. If locale is tr, output every user-facing string in Turkish only. Do not use English words except Latin scientific plant names. User notes: {notes or 'none'}. Determine whether the image is plant-related."
        return PlantScreenResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def identify(self, image_url: str, locale: str = "tr", notes: str | None = None) -> IdentifyResponse:
        instruction = 'Return only valid JSON: {"common_name": string, "scientific_name": string, "confidence": integer 0-100, "short_description": string}.'
        user_text = f"Language: {locale}. If locale is tr, common_name and short_description must be Turkish only; scientific_name stays Latin. Do not output English common names. User notes: {notes or 'none'}. Identify the plant."
        return IdentifyResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def diagnose(self, image_url: str, locale: str = "tr", plant_name: str | None = None, notes: str | None = None) -> DiagnoseResponse:
        instruction = 'Return only valid JSON: {"health_score": integer 0-100, "severity": "low"|"medium"|"high"|"critical", "diagnosis_summary": string, "likely_causes": [{"title": string, "confidence": integer 0-100, "explanation": string}], "immediate_actions": [string], "avoid_actions": [string]}.'
        user_text = f"Language: {locale}. If locale is tr, diagnosis_summary, likely_causes, immediate_actions and avoid_actions must be Turkish only. Keep them simple, actionable and understandable for a non-expert plant owner. Plant hint: {plant_name or 'unknown'}. User notes: {notes or 'none'}. Diagnose the plant."
        return DiagnoseResponse.model_validate(self._responses_json(instruction, user_text, image_url))

    def care_plan(self, locale: str, plant_name: str, diagnosis_summary: str, health_score: int, notes: str | None = None) -> CarePlanResponse:
        instruction = 'Return only valid JSON: {"today": [{"title": string, "details": string}], "this_week": [{"title": string, "details": string}], "next_check_in_days": integer, "long_term_tips": [string]}.'
        user_text = f"Language: {locale}. If locale is tr, all task titles, details and tips must be Turkish only. Use short practical sentences. Plant: {plant_name}. Health score: {health_score}. Diagnosis: {diagnosis_summary}. Notes: {notes or 'none'}. Create a simple care plan."
        return CarePlanResponse.model_validate(self._responses_json(instruction, user_text))

    def plant_parent_profile(self, locale: str, plant_name: str, diagnosis_summary: str, notes: str | None = None) -> PlantParentProfileResponse:
        instruction = 'Return only valid JSON: {"placement": "indoor"|"balcony"|"garden"|"mixed", "placement_advice": string, "pet_safety": string, "child_safety": string, "vacation_tip": string, "soil_tip": string, "watering_tip": string, "watering_interval_days": integer, "soil_change_interval_days": integer}.'
        user_text = f"Language: {locale}. If locale is tr, all guidance strings must be Turkish only. Do not use English. Plant: {plant_name}. Diagnosis: {diagnosis_summary}. Notes: {notes or 'none'}. Create home care guidance."
        return PlantParentProfileResponse.model_validate(self._responses_json(instruction, user_text))


def _plant_live_system(locale: str) -> str:
    if locale == "tr":
        return (
            "Sen Botanistiq uygulamasındaki CANLI AI bitki asistanısın. "
            "Her istek OpenAI üzerinden yeni cevap üretir; şablon veya sabit cevap verme. "
            "Sadece seçili kayıtlı bitki veya bu oturumda yüklenen fotoğraflar hakkında cevap ver. "
            "Konu dışı soruları kibarca reddet. Önceki cevapları tekrar etme. "
            "Son kullanıcının son sorusunu doğrudan cevapla. Cevap Türkçe, kısa, net ve uygulanabilir olsun. "
            "Gerekiyorsa 'şimdi yap' adımını bir cümleyle söyle. Emin olmadığın görsel bulguyu kesin hastalık gibi söyleme."
        )
    return (
        "You are the LIVE AI plant assistant inside Botanistiq. "
        "Generate a fresh OpenAI answer for every request; do not use fixed templates. "
        "Answer only about the selected saved plant or uploaded photos in this session. "
        "Refuse unrelated topics. Do not repeat previous answers. Answer the latest user question directly, briefly and actionably."
    )

def _plant_context_text(scope_label: str, plant: dict | None, photo_count: int) -> str:
    plant = plant or {}
    return (
        f"Selected scope: {scope_label}\n"
        f"Plant name: {plant.get('name', scope_label)}\n"
        f"Health score: {plant.get('health_score', 'unknown')}\n"
        f"Severity: {plant.get('severity', 'unknown')}\n"
        f"Diagnosis summary: {plant.get('diagnosis_summary', '')}\n"
        f"Likely causes: {plant.get('likely_causes', [])}\n"
        f"Immediate actions: {plant.get('immediate_actions', [])}\n"
        f"Avoid actions: {plant.get('avoid_actions', [])}\n"
        f"Watering tip: {plant.get('watering_tip', '')}\n"
        f"Soil tip: {plant.get('soil_tip', '')}\n"
        f"Light advice: {plant.get('light_advice', '')}\n"
        f"Placement advice: {plant.get('placement_advice', '')}\n"
        f"Uploaded photo count: {photo_count}\n"
    )

def _is_live_chat_off_topic(question: str) -> bool:
    q = question.lower()
    blocked = [
        "bitcoin", "kripto", "crypto", "borsa", "hisse", "futbol", "maç", "mac",
        "siyaset", "seçim", "secim", "kod", "flutter", "python", "hava durumu",
        "film", "dizi", "aşk", "ask", "ilişki", "iliski", "yemek tarifi",
    ]
    return any(item in q for item in blocked)

def _live_photo_chat(self, payload) -> str:
    question = (payload.question or "").strip()
    if not question:
        return "Lütfen bu bitki hakkında bir soru yaz."

    system = payload.system_instruction or _plant_live_system(payload.locale)
    max_photos = 1
    photos = (payload.photos or [])[:max_photos]
    history = (payload.history or [])[-4:]

    history_text = "\n".join(
        [
            f"{getattr(item, 'role', 'user')}: {getattr(item, 'text', '')[:500]}"
            for item in history
            if getattr(item, "text", "").strip()
        ]
    )

    content = [{
        "type": "input_text",
        "text": (
            system + "\n\n"
            "IMPORTANT:\n"
            "- This is a real live AI chat request. Produce a new answer now.\n"
            "- Do not repeat the previous assistant answer.\n"
            "- The latest question is authoritative.\n"
            "- If locale is tr, answer in Turkish only except Latin scientific names.\n\n"
            + _plant_context_text(payload.scopeLabel, payload.plant, len(photos)) +
            "\nPrevious chat context (do not repeat, only use for continuity):\n" + history_text +
            "\n\nLATEST USER QUESTION:\n" + question +
            "\n\nAnswer only about this selected plant or uploaded photos. Keep it concise and specific."
        ),
    }]
    for photo in photos:
        if photo.base64:
            content.append({
                "type": "input_image",
                "image_url": f"data:{photo.mimeType};base64,{photo.base64}",
            })

    response = self.client.responses.create(
        model=self.model,
        input=[{"role": "user", "content": content}],
        instructions=system,
        temperature=0.35,
        max_output_tokens=260,
    )
    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI response did not include output_text.")
    return text.strip()

OpenAIPlantService.live_photo_chat = _live_photo_chat
