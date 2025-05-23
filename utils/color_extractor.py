from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

def rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(*rgb)

def get_dominant_color(image_file, k=5, image_resize=(100, 100)):
    if not isinstance(image_file, Image.Image):
        image_file = Image.open(image_file)

    image = image_file.convert("RGBA").resize(image_resize)

    pixels = np.array(image)
    pixels = pixels.reshape(-1, 4)
    pixels = pixels[pixels[:, 3] > 0]  # Keep pixels with alpha > 0

    if pixels.size == 0:
        return "#000000"

    pixels_rgb = pixels[:, :3]

    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(pixels_rgb)

    counts = np.bincount(kmeans.labels_)
    dominant_color = kmeans.cluster_centers_[np.argmax(counts)].astype(int)

    return rgb_to_hex(dominant_color)
