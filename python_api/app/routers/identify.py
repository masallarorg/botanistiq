from fastapi import APIRouter
from app.schemas.common import ImageAnalyzeRequest

router = APIRouter()

@router.post('/identify')
def identify_plant(payload: ImageAnalyzeRequest):
    return {
        'scan_id': 'demo-scan-1',
        'species_name': 'Monstera deliciosa',
        'common_name': 'Deve tabanı',
        'confidence': 0.86,
        'short_summary': 'Aydınlık dolaylı ışığı seven popüler bir iç mekan bitkisi.',
        'care_highlights': ['Toprak hafif kurudukça sula', 'Dolaylı parlak ışık ver'],
        'warning_notes': ['Düşük kalite görselde sonuç sapabilir']
    }
