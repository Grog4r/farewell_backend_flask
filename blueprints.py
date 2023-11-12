import base64
import sys
from datetime import datetime
from io import BytesIO

from flask import Blueprint, Response, current_app, make_response, request, send_file
from PIL import Image

from database import (
    get_all_resources,
    get_resource_file,
    get_resource_metadata,
    store_file,
    upload_resource_metadata,
)
from entities import ResourceFile, ResourceMetadata

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


@blueprint_backend.route("/upload", methods=["POST"])
def blueprint_upload_resource():
    inputs = {
        "file": request.files["file"],
        "file_name": request.files["file"].filename,
        "password": request.form.get("password"),
        "creation_date": datetime.strptime(
            request.form.get("creation_date"), "%Y-%m-%d"
        ).date(),
        "caption": request.form.get("caption"),
        "uploaded_by": request.form.get("uploaded_by"),
    }

    print(inputs, file=sys.stderr)

    for key, value in inputs.items():
        if value is None:
            raise ValueError(f"The form parameter '{key}' must be provided.")

    resource_metadata = ResourceMetadata(
        inputs["file_name"],
        inputs["creation_date"],
        inputs["caption"],
        inputs["uploaded_by"],
    )

    file_resource = ResourceFile(uuid=resource_metadata.uuid, file=inputs["file"])

    metadata_result = upload_resource_metadata(resource_metadata)
    store_file(file_resource)

    return metadata_result
