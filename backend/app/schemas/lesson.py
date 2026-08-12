from pydantic import BaseModel


class VideoUrlResponse(BaseModel):
    url: str
    expires_in: int


class ThumbnailUrlResponse(BaseModel):
    url: str
    expires_in: int
