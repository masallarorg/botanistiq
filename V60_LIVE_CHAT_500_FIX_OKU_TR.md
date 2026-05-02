# Botanistiq V60 - Canlı AI Sohbet 500 Fix

Render loglarında canlı sohbet endpointi artık 404 değil 500 veriyor.
Bu, endpointin çalıştığını ama OpenAI çağrısı içinde hata oluştuğunu gösterir.

## Yapılan teknik düzeltme

`/api/v1/plant-live-photo-chat` artık OpenAI `responses.create` yerine daha stabil olan:

```python
client.chat.completions.create(...)
```

ile çalışır.

Bu canlı sohbet için daha güvenlidir, çünkü:

- Text-only kayıtlı bitki sohbetinde stabil çalışır.
- Fotoğraf varsa vision formatı `image_url` ile gönderilir.
- OpenAI SDK 1.59.6 ile uyumludur.
- Render loglarına gerçek exception yazılır.

## Render ayarı

Environment içinde mutlaka:

```text
PYTHON_VERSION = 3.11.9
OPENAI_API_KEY = sk-...
OPENAI_MODEL = gpt-4o-mini
ALLOWED_ORIGINS = *
```

Build:

```text
pip install --upgrade pip && pip install -r requirements.txt
```

Start:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Deploy:

```text
Manual Deploy > Clear build cache & deploy
```
