import mimetypes
import os
import sys
from pathlib import Path

import httpx

API_BASE_URL = "http://localhost:8000/api/v1"


def upload_video(slug: str, path: str):
    admin_email = os.environ["ADMIN_EMAIL"]
    admin_password = os.environ["ADMIN_PASSWORD"]

    file_path = Path(path)
    content_type = mimetypes.guess_type(file_path.name)[0]

    with httpx.Client(timeout=120) as client:
        login_response = client.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": admin_email, "password": admin_password},
        )
        login_response.raise_for_status()

        with file_path.open("rb") as f:
            response = client.post(
                f"{API_BASE_URL}/admin/lessons/{slug}/video",
                files={"file": (file_path.name, f, content_type)},
            )

    response.raise_for_status()
    print(f"video_key: {response.json()['video_key']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.upload_video <slug> <path>")
        sys.exit(1)
    upload_video(sys.argv[1], sys.argv[2])
