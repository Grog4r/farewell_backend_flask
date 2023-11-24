import base64
import json
import os
import sys
from datetime import date, datetime
from io import BytesIO

import jwt
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
    session,
)
from flask_httpauth import HTTPBasicAuth
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    delete_image_by_uuid,
    get_all_resources,
    get_all_unlocked_resources_and_the_next_locked_one,
    get_resource_file,
    get_resource_metadata,
    get_resource_metadata_json,
    store_file,
    update_resource_metadata,
    upload_resource_metadata,
)
from entities import ResourceFile, ResourceMetadata
from utils import IMAGE_FORMAT_MAPPING, MIMETYPE_MAPPING, thumbnail_image

blueprint_backend = Blueprint("backend", __name__)


auth = HTTPBasicAuth()

JWT_SECRET = os.environ.get("JWT_SECRET")


class AuthenticationError(Exception):
    pass


def verify_jwt(request):
    if "token" in session:
        jwt_decoded = jwt.decode(session["token"], JWT_SECRET, algorithms=["HS256"])
        if not jwt_decoded["user"] in json.loads(os.environ.get("USERS")).keys():
            raise AuthenticationError("Your session token seems to be broken!")
    else:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError("You cannot access this without an authorization header!")
        jwt_token = auth_header.split("Bearer ")[1]
        jwt_decoded = jwt.decode(jwt_token, JWT_SECRET, algorithms=["HS256"])
        # print(jwt_decoded, file=sys.stderr)
        api_key = os.environ.get("API_KEY")
        if not jwt_decoded["api_key"] == api_key:
            raise AuthenticationError("Your JWT Token does not have a valid API Key!")
    return True


@auth.verify_password
def verify_password(username: str, password: str) -> bool:
    users = json.loads(os.environ.get("USERS"))

    login_successful = username in users and check_password_hash(
        users.get(username), password
    )
    if login_successful:
        session["token"] = jwt.encode({"user": username}, JWT_SECRET, algorithm="HS256")
    return login_successful


@blueprint_backend.route("/", methods=["GET"])
def blueprint_get_all_available_resources():
    if not verify_jwt(request):
        raise AuthenticationError("Something went wrong with the authentication!")

    return get_all_unlocked_resources_and_the_next_locked_one()


@blueprint_backend.route("/meta", methods=["GET"])
def blueprint_get_resource_meta(uuid=None):
    if not verify_jwt(request):
        raise AuthenticationError("Something went wrong with the authentication!")

    if not uuid:
        uuid = request.args["uuid"]
    if not uuid:
        raise ValueError("Please provide the uuid.")
    meta = get_resource_metadata_json(uuid)
    if not meta:
        raise FileNotFoundError(f"The meta with uuid {uuid} does not exist.")

    return meta


@blueprint_backend.route("/resource", methods=["GET"])
def blueprint_get_resource_file(uuid=None):
    if not verify_jwt(request):
        raise AuthenticationError("Something went wrong with the authentication!")

    if not uuid:
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

    mimetype = MIMETYPE_MAPPING[file_ending.lower()]
    print(f"{file_name}: {mimetype}", file=sys.stderr)
    return send_file(image_stream, mimetype=mimetype, download_name=file_name)


@blueprint_backend.route("/uploader", methods=["GET", "POST"])
@auth.login_required
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
                "uploader.html",
                result="Der Upload war erfolgreich! 🥳",
                name=auth.current_user(),
            )
        else:
            return render_template(
                "uploader.html",
                result="Da ist etwas schief gelaufen! 🤯",
                name=auth.current_user(),
            )

    # If it's a GET request, render the uploader html page
    return render_template(
        "uploader.html",
        result="Uploade ein Bild für Flo! 🖼️",
        name=auth.current_user(),
    )


@blueprint_backend.route("/manage", methods=["GET"])
@auth.login_required
def show_images():
    resources = get_all_resources()
    return render_template("show_images.html", images=resources)


@blueprint_backend.route("/edit_image", methods=["GET", "POST"])
@auth.login_required
def edit_image(uuid=None):
    if request.method == "POST":
        uuid = request.form.get("uuid")
        title = request.form.get("title")
        caption = request.form.get("caption")
        uploaded_by = request.form.get("uploaded_by")
        creation_date = request.form.get("creation_date")
        try:
            creation_date = datetime.fromisoformat(creation_date).date()
        except Exception as e:
            image_metadata = get_resource_metadata(uuid)
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
@auth.login_required
def delete_image(uuid=None):
    if not uuid:
        uuid = request.args["uuid"]
    if not uuid:
        raise ValueError("Please provide the uuid.")

    delete_image_by_uuid(uuid)

    response_data = {"message": "Image deleted successfully"}

    return jsonify(response_data), 302, {"Location": "/manage"}
