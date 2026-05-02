$ErrorActionPreference = "Stop"

if (!(Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host ".env dosyasi olusturuldu. Lutfen OPENAI_API_KEY degerini doldur." -ForegroundColor Yellow
}

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\activate
pip install -r requirements.txt

Write-Host "Backend baslatiliyor: http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "Telefon test URL ornegi: http://BILGISAYAR_IP:8000/health" -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
