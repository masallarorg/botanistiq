# Botanistiq V57 Backend Kök Paket

Bu zip'i mevcut backend repo klasörüne aç:

```powershell
C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
```

Sonra:

```powershell
cd C:\Users\serkan\OneDrive\Desktop\botanistiq_ui_kit\backend
git add .
git commit -m "V57 real live AI chat backend"
git push
```

Render otomatik deploy etmezse:

```text
Render > botanistiq-api > Manual Deploy > Deploy latest commit
```

Test:

```text
https://botanistiq-api.onrender.com/api/v1/health
```

Canlı sohbet endpointi POST endpointtir:

```text
POST https://botanistiq-api.onrender.com/api/v1/plant-live-photo-chat
```
