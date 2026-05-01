from pydantic import BaseModel, HttpUrl

class ImageAnalyzeRequest(BaseModel):
    user_id: str
    image_url: HttpUrl
    locale: str = "tr"
