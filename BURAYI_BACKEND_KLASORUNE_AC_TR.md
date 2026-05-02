# Bu ZIP sadece backend içindir

Bu paketi şu klasörün içine aç:

```powershell
C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
```

Açınca klasör yapısı şöyle olmalı:

```text
backend/
  app/
  python_api/
  scripts/
  requirements.txt
  .env.example
  .gitignore
```

Yani `mobile_app` klasörü bu pakette yoktur.

## GitHub'a gönder

```powershell
cd C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
git status
git add .
git commit -m "V50 backend live AI chat endpoint"
git push
```

## Render

Push sonrası Render otomatik deploy eder. Etmezse:

```text
Render > botanistiq-api > Manual Deploy > Deploy latest commit
```

## Test

```text
https://botanistiq-api.onrender.com/api/v1/health
```

Canlı AI sohbet endpointi POST endpointtir:

```text
POST https://botanistiq-api.onrender.com/api/v1/plant-live-photo-chat
```

## Güvenlik

`.env` bu pakette yoktur. OpenAI key sadece Render Environment Variables içinde durmalı.
