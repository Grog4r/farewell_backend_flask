import base64
import os
import sys
from datetime import date, datetime
from io import BytesIO

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
)
from PIL import Image
from werkzeug.datastructures import FileStorage

from database import (
    delete_image_by_uuid,
    get_all_resources,
    get_resource_file,
    get_resource_metadata,
    store_file,
    update_resource_metadata,
    upload_resource_metadata,
)
from entities import ResourceFile, ResourceMetadata
from utils import IMAGE_FORMAT_MAPPING, MIMETYPE_MAPPING, thumbnail_image

TMP_FOLDER = "/tmp/farewell"

blueprint_backend = Blueprint("backend", __name__)


@blueprint_backend.route("/", methods=["GET"])
def blueprint_get_all_available_resources():
    return get_all_resources()


@blueprint_backend.route("/resource", methods=["GET"])
def blueprint_get_resource_file(uuid=None):
    if not uuid:
        uuid = request.args["uuid"]
    if not uuid:
        raise ValueError("Please provide the uuid.")
    image_data = get_resource_file(uuid)
    print(len(image_data), file=sys.stderr)
    if not image_data:
        raise FileNotFoundError(f"The file with uuid {uuid} does not exist.")
    image_metadata = get_resource_metadata(uuid)
    image_stream = BytesIO(image_data)
    file_name = image_metadata["file_name"]
    file_ending = file_name.split(".")[-1]

    mimetype = MIMETYPE_MAPPING[file_ending.lower()]
    print(f"{file_name}: {mimetype}", file=sys.stderr)
    return send_file(image_stream, mimetype=mimetype, download_name=file_name)


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

        if inputs["file_name"].split(".")[1].lower() not in MIMETYPE_MAPPING.keys():
            return render_template(
                "uploader.html",
                result="Bitte verwende nur Bilder im Format PNG oder JPEG! ⚠️",
            )

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
            downscaled_img = thumbnail_image(img)
            image_io = BytesIO()

            file_name = request.files["file"].filename
            file_ending = file_name.split(".")[1]
            image_format = IMAGE_FORMAT_MAPPING[file_ending]
            mimetype = MIMETYPE_MAPPING[file_ending.lower()]

            print(
                f"Saving img {file_name}: {image_format}, {mimetype}", file=sys.stderr
            )
            downscaled_img.save(image_io, format=image_format)
            image_io.seek(0)  # Reset the BytesIO position to the beginning
            image_file = FileStorage(
                stream=image_io,
                filename=file_name,
                content_type=mimetype,
            )
        except KeyError as key_error:
            print(key_error, file=sys.stderr)
        except Exception as e:
            print(e, file=sys.stderr)

        file_resource = ResourceFile(uuid=resource_metadata.uuid, file=image_file)

        metadata_result = upload_resource_metadata(resource_metadata)
        metadata_file_result = store_file(file_resource)
        if metadata_result["uuid"] and metadata_file_result["uuid"]:
            return render_template(
                "uploader.html", result="Der Upload war erfolgreich! 🥳"
            )
        else:
            return render_template(
                "uploader.html", result="Da ist etwas schief gelaufen! 🤯"
            )

    # If it's a GET request, render the uploader html page
    return render_template("uploader.html", result="Uploade ein Bild für Flo! 🖼️")


@blueprint_backend.route("/manage", methods=["GET"])
def show_images():
    resources = get_all_resources()
    return render_template("show_images.html", images=resources)


@blueprint_backend.route("/edit_image", methods=["GET", "POST"])
def edit_image(uuid=None):
    if request.method == "POST":
        uuid = request.form.get("uuid")
        title = request.form.get("title")
        caption = request.form.get("caption")
        uploaded_by = request.form.get("uploaded_by")
        creation_date = request.form.get("creation_date")
        try:
            creation_date = datetime.strptime(creation_date, "%d.%m.%Y")
            creation_date = date.strftime(creation_date, "%d.%m.%Y")
        except Exception as e:
            return render_template("edit_image.html", image=image_metadata, error=e)

        image_metadata = update_resource_metadata(
            uuid, title, caption, uploaded_by, creation_date
        )
        return redirect("/manage")
    else:
        if not uuid:
            uuid = request.args["uuid"]
        if not uuid:
            raise ValueError("Please provide the uuid.")

        image_metadata = get_resource_metadata(uuid)
        return render_template("edit_image.html", image=image_metadata, error="")


@blueprint_backend.route("/delete_image", methods=["DELETE"])
def delete_image(uuid=None):
    if not uuid:
        uuid = request.args["uuid"]
    if not uuid:
        raise ValueError("Please provide the uuid.")

    delete_image_by_uuid(uuid)

    response_data = {"message": "Image deleted successfully"}

    return jsonify(response_data), 302, {"Location": "/manage"}
