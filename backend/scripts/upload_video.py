import mimetypes
import sys
from pathlib import Path

import httpx

from app.config import settings

API_BASE_URL = "http://localhost:8000/api/v1"


def upload_video(slug: str, path: str):
    file_path = Path(path)
    content_type = mimetypes.guess_type(file_path.name)[0]

    with file_path.open("rb") as f:
        response = httpx.post(
            f"{API_BASE_URL}/admin/lessons/{slug}/video",
            headers={"X-Upload-Secret": settings.upload_secret},
            files={"file": (file_path.name, f, content_type)},
            timeout=120,
        )

    response.raise_for_status()
    print(f"video_key: {response.json()['video_key']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.upload_video <slug> <path>")
        sys.exit(1)
    upload_video(sys.argv[1], sys.argv[2])
