from fastapi import FastAPI
from app.routers.identify import router as identify_router
from app.routers.diagnose import router as diagnose_router
from app.routers.care_plan import router as care_plan_router

app = FastAPI(title="GreenMind API", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(identify_router, prefix="/v1", tags=["identify"])
app.include_router(diagnose_router, prefix="/v1", tags=["diagnose"])
app.include_router(care_plan_router, prefix="/v1", tags=["care-plan"])
