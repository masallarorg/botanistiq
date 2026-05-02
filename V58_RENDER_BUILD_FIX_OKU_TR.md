# Botanistiq V58 Render Build Fix Backend

Bu paket Render build hatalarını azaltmak için hazırlandı.

## Değişiklikler

- `runtime.txt` eklendi: Python 3.11.9
- `requirements.txt` sadeleştirildi:
  - fastapi
  - uvicorn
  - openai
  - pydantic
  - pydantic-settings
  - python-dotenv
- Backend için gerekmeyen `firebase-admin` kaldırıldı.
- `render.yaml` Python servis ve doğru start command ile güncellendi.
- Dockerfile da `uvicorn app.main:app` kullanacak şekilde düzeltildi.

## Nereye açılacak?

Şu klasöre aç:

```powershell
C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
```

## Sonra GitHub'a gönder

```powershell
cd C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
git add .
git commit -m "V58 render build fix live chat backend"
git push
```

## Render ayarları

Render > botanistiq-api > Settings:

```text
Root Directory:
boş

Build Command:
pip install --upgrade pip && pip install -r requirements.txt

Start Command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Deploy:

```text
Manual Deploy > Clear build cache & deploy
```

## Test

```powershell
Invoke-RestMethod -Uri "https://botanistiq-api.onrender.com/api/v1/health"
```
