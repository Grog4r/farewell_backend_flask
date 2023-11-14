import sys
from datetime import date

from PIL import Image

IMAGE_FORMAT_MAPPING = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
}

MIMETYPE_MAPPING = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}


def calculate_unlock_date(creation_date: date, leave_date: date) -> date:
    unlock_date = date(day=creation_date.day, month=creation_date.month, year=2023)
    if unlock_date < leave_date:
        unlock_date = date(day=creation_date.day, month=creation_date.month, year=2024)
    return unlock_date

def thumbnail_image(img: Image) -> Image:
    print(img.width, img.height, file=sys.stderr)
    img.thumbnail((1920, 1920))
    print(img.width, img.height, file=sys.stderr)
    return img
