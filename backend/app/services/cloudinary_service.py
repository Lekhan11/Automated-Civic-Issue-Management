import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from app.core.config import settings
from typing import List

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)


async def upload_images(files: List[UploadFile]) -> List[str]:
    """Upload multiple images to Cloudinary and return their URLs."""
    urls = []
    for file in files:
        contents = await file.read()
        result = cloudinary.uploader.upload(
            contents,
            folder="complaints",
            resource_type="image",
        )
        urls.append(result["secure_url"])
        await file.seek(0)  # Reset file pointer
    return urls


async def delete_image(public_id: str) -> bool:
    """Delete an image from Cloudinary."""
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False