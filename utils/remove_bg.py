from PIL import Image
from rembg import remove
import io

def remove_background(image_file):
    # Read image bytes
    image_bytes = image_file.read()

    # Remove background using rembg
    bg_removed_bytes = remove(image_bytes)

    # Convert bytes to a PIL.Image (with alpha for transparency)
    image = Image.open(io.BytesIO(bg_removed_bytes)).convert("RGBA")

    return image
