# Botanistiq Backend

Bu klasör artık hem senin verdiğin backend yapısını hem de canlı AI sohbet endpointlerini içerir.

## Endpointler

```text
GET  /health
GET  /api/v1/health
GET  /api/v1/mounted-backend-status
POST /api/v1/plant-live-photo-chat
POST /api/v1/analyze-plant
POST /api/v1/screen-plant
POST /api/v1/scan-analyze
```

Mobil canlı sohbet `/api/v1/plant-live-photo-chat` kullanır. Monte edilen backend ise `screen-plant` ve `scan-analyze` endpointlerini sağlar.

## Local çalıştırma

```powershell
cd C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\mobile_app\flutter_app\backend
copy .env.example .env
notepad .env
powershell -ExecutionPolicy Bypass -File .\run_local_windows.ps1
```

`.env` içine `OPENAI_API_KEY` yaz.

## Flutter local

```powershell
flutter run --dart-define=BOTANISTIQ_API_URL=http://BILGISAYAR_IP:8000
```

## Production

```powershell
flutter build appbundle --release --dart-define=BOTANISTIQ_API_URL=https://api.botanistiq.app
```

OpenAI key Flutter içine yazılmaz; sadece backend environment variable içinde tutulur.
