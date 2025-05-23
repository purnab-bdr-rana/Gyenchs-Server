import hashlib

def calculate_image_hash(file):
    file.seek(0)
    file_bytes = file.read()
    file.seek(0)
    return hashlib.sha256(file_bytes).hexdigest()
