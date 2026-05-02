# Botanistiq V59 Render Python Version Fix

Render build logunda Python 3.14 kullanıldığı görülüyor:

```text
/interpreter ... python3.14
pydantic-core ... maturin ... read-only file system
```

Bu paket Python sürümünü 3.11.9'a sabitlemek için hazırlandı.

## Eklenen / düzeltilen dosyalar

```text
.python-version      -> 3.11.9
runtime.txt          -> python-3.11.9
render.yaml          -> PYTHON_VERSION=3.11.9
requirements.txt     -> Python 3.11 uyumlu stabil paketler
```

## Render Dashboard'da mutlaka yapılacak ek ayar

Render > botanistiq-api > Environment:

```text
PYTHON_VERSION = 3.11.9
OPENAI_API_KEY = sk-...
OPENAI_MODEL = gpt-4o-mini
ALLOWED_ORIGINS = *
```

Sonra:

```text
Manual Deploy > Clear build cache & deploy
```

## Build Command

```text
pip install --upgrade pip && pip install -r requirements.txt
```

## Start Command

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
