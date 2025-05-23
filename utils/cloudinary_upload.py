import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import uuid
from datetime import datetime


# Configure Cloudinary (use env variables in production)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def upload_image_to_cloudinary(image_file, user_id, subfolder="profile", is_unique=False):
    """
    Uploads and compresses an image to Cloudinary.
    - Profile: overwrites old image
    - Attire: adds new compressed image
    """
    try:
        cloudinary_path = f"gyencha/{user_id}/{subfolder}"

        if is_unique:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{timestamp}_{unique_id}"
            overwrite = False
        else:
            filename = "profile_img"
            overwrite = True

        result = cloudinary.uploader.upload(
            image_file,
            folder=cloudinary_path,
            public_id=filename,
            overwrite=overwrite,
            resource_type="image",
            transformation=[
                {"quality": "auto", "fetch_format": "auto", "crop": "limit", "width": 400, "height": 400}
            ]
        )

        return result.get("secure_url")

    except Exception as e:
        raise Exception(f"Cloudinary upload failed: {str(e)}")
