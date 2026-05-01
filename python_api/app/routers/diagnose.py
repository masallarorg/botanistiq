from fastapi import APIRouter
from app.schemas.common import ImageAnalyzeRequest

router = APIRouter()

@router.post('/diagnose')
def diagnose_plant(payload: ImageAnalyzeRequest):
    return {
        'scan_id': 'demo-scan-2',
        'suspected_issues': ['Aşırı sulama ihtimali', 'Düşük ışık stresi'],
        'confidence': 0.71,
        'recommended_actions': ['Sulama sıklığını azalt', 'Daha aydınlık konuma taşı'],
        'urgency_level': 'medium'
    }
