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

from database import (
    get_all_resources,
    get_resource_file,
    get_resource_metadata,
    store_file,
    upload_resource_metadata,
)
from entities import ResourceFile, ResourceMetadata

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
    mimetype_mapping = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    mimetype = mimetype_mapping[file_ending]
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
            # "password": request.form.get("password"),
            "creation_date": creation_date,
            "title": request.form.get("title"),
            "caption": request.form.get("caption"),
            "uploaded_by": request.form.get("uploaded_by"),
        }

        required = [
            "file",
            # "password",
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

        file_resource = ResourceFile(uuid=resource_metadata.uuid, file=inputs["file"])

        metadata_result = upload_resource_metadata(resource_metadata)
        store_file(file_resource)

        return metadata_result

        # Perform necessary operations with the form data (e.g., save to database, process image, etc.)

        # For demonstration purposes, let's just print the information
        print(f"File: {uploaded_file.filename}")
        print(f"Title: {title}")
        print(f"Caption: {caption}")
        print(f"Uploaded by: {uploaded_by}")

        # You can redirect to another page or render a success message
        return "Form submitted successfully!"

    # If it's a GET request, render the form
    return render_template("uploader.html")
