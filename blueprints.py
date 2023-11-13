import base64
import os
import sys
from datetime import datetime
from io import BytesIO

from flask import (
    Blueprint,
    Response,
    current_app,
    make_response,
    render_template,
    request,
    send_file,
)
from PIL import Image
from werkzeug.datastructures import FileStorage

from database import (
    get_all_resources,
    get_resource_file,
    get_resource_metadata,
    store_file,
    upload_resource_metadata,
)
from entities import ResourceFile, ResourceMetadata
from utils import IMAGE_FORMAT_MAPPING, MIMETYPE_MAPPING, downscale_image

TMP_FOLDER = "/tmp/farewell"

blueprint_backend = Blueprint("backend", __name__)


@blueprint_backend.route("/", methods=["GET"])
def blueprint_get_all_available_resources():
    return get_all_resources()


@blueprint_backend.route("/resource", methods=["GET"])
def blueprint_get_resource_file():
    uuid = request.args["uuid"]
    if not uuid:
        raise ValueError("Please provide the uuid.")
    image_data = get_resource_file(uuid)
    if not image_data:
        raise FileNotFoundError(f"The file with uuid {uuid} does not exist.")
    image_metadata = get_resource_metadata(uuid)
    image_stream = BytesIO(image_data)
    file_name = image_metadata["file_name"]
    file_ending = file_name.split(".")[-1]

    mimetype = MIMETYPE_MAPPING[file_ending]
    return send_file(image_stream, mimetype=mimetype, download_name="image.png")


@blueprint_backend.route("/uploader", methods=["GET", "POST"])
def uploader():
    if request.method == "POST":
        creation_date = datetime.strptime(
            request.form.get("creation_date"), "%d.%m.%Y"
        ).date()

        inputs = {
            "file": request.files["file"],
            "file_name": request.files["file"].filename,
            "creation_date": creation_date,
            "title": request.form.get("title"),
            "caption": request.form.get("caption"),
            "uploaded_by": request.form.get("uploaded_by"),
        }

        required = [
            "file",
            "creation_date",
            "title",
            "uploaded_by",
        ]

        print(inputs, file=sys.stderr)

        for key in required:
            if not inputs[key]:
                raise ValueError(f"The form parameter '{key}' must be provided.")

        resource_metadata = ResourceMetadata(
            inputs["file_name"],
            inputs["creation_date"],
            inputs["title"],
            inputs["caption"],
            inputs["uploaded_by"],
        )

        image_file = inputs["file"]

        try:
            img = Image.open(image_file)
            if img.size[0] > 1920 or img.size[1] > 1920:
                downscaled_img = downscale_image(img)
                image_io = BytesIO()

                file_name = request.files["file"].filename
                file_ending = file_name.split(".")[1]
                image_format = IMAGE_FORMAT_MAPPING[file_ending]
                mimetype = MIMETYPE_MAPPING[file_ending]

                downscaled_img.save(image_io, format=image_format)
                image_io.seek(0)  # Reset the BytesIO position to the beginning
                image_file = FileStorage(
                    stream=image_io,
                    filename=file_name,
                    content_type=mimetype,
                )
        except Exception as e:
            print(e, file=sys.stderr)

        file_resource = ResourceFile(uuid=resource_metadata.uuid, file=image_file)

        metadata_result = upload_resource_metadata(resource_metadata)
        store_file(file_resource)

        return metadata_result

    # If it's a GET request, render the uploader html page
    return render_template("uploader.html")
