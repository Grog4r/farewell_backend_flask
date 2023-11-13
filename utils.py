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


def downscale_image(img: Image, target_resolution=(1920, 1080)) -> Image:
    # Get the current width and height
    width, height = img.size

    # Calculate the aspect ratio
    aspect_ratio = width / height

    # Calculate the new size based on the target resolution and aspect ratio
    if aspect_ratio > 1:  # Horizontal image
        new_width = target_resolution[0]
        new_height = int(new_width / aspect_ratio)
    else:  # Vertical image
        new_height = target_resolution[1]
        new_width = int(new_height * aspect_ratio)

    # Resize the image
    resized_img = img.resize((new_width, new_height))

    # Create a new blank image with the target resolution
    result_img = Image.new("RGB", target_resolution, (255, 255, 255))

    # Calculate the position to paste the resized image
    paste_position = (
        (target_resolution[0] - new_width) // 2,
        (target_resolution[1] - new_height) // 2,
    )

    # Paste the resized image onto the blank image
    result_img.paste(resized_img, paste_position)

    return result_img
