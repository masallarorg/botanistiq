from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class CarePlanRequest(BaseModel):
    user_id: str
    species_name: str
    environment: str
    locale: str = 'tr'

@router.post('/care-plan')
def build_care_plan(payload: CarePlanRequest):
    return {
        'watering': 'Toprak üst kısmı kurudukça sulama',
        'sunlight': 'Parlak ama dolaylı ışık',
        'humidity': 'Orta-yüksek nem',
        'fertilizer': 'Büyüme döneminde ayda 1',
        'seasonal_notes': 'Kışın sulamayı azalt',
        'reminders': ['3 günde nem kontrolü', '7 günde sulama kontrolü']
    }
