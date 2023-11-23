import base64
import json
import os
import sys
from datetime import date

import bson
import pymongo
from bson import json_util
from bson.binary import Binary
from flask import send_file
from werkzeug.datastructures import FileStorage

from entities import ResourceFile, ResourceMetadata
from utils import calculate_unlock_date

mongodb_connection_url = "mongodb://your_username:your_password@mongodb:27017/"
mongodb_password = os.environ.get("MONGODB_PASSWORD")
if mongodb_password:
    mongodb_connection_url = f"mongodb+srv://niklaskuchenspam:{mongodb_password}@farewellmongodb.zohoneg.mongodb.net/?retryWrites=true&w=majority"

print(f"Connecting to MongoDB at: {mongodb_connection_url.split('@')[1]}", file=sys.stderr)
client = pymongo.MongoClient(mongodb_connection_url)

db = client["database"]


def upload_resource_metadata(resource: ResourceMetadata) -> dict:
    resource_metadata_collection = db["resource_metadata"]
    _id = resource_metadata_collection.insert_one(resource.to_dict())
    if _id.inserted_id is not None:
        return resource.to_dict()


def store_file(file: ResourceFile) -> dict:
    resource_files_collection = db["resource_files"]
    _id = resource_files_collection.insert_one(file.to_dict())
    if _id.inserted_id is not None:
        return file.to_dict()


def get_all_resources() -> list:
    resource_metadata_collection = db["resource_metadata"]

    cursor = resource_metadata_collection.find({})
    return_list = []
    for res in cursor:
        json_res = parse_json(res)
        del json_res["_id"]
        return_list.append(json_res)
    return return_list


def get_all_unlocked_resources_and_the_next_locked_one() -> list:
    resource_metadata_collection = db["resource_metadata"]
    query = {"unlock_date": {"$lte": date.today().isoformat()}}

    cursor = resource_metadata_collection.find(query, sort=[("unlock_date", 1)])
    return_list = []
    for res in cursor:
        json_res = parse_json(res)
        del json_res["_id"]
        return_list.append(json_res)

    query = {"unlock_date": {"$gt": date.today().isoformat()}}
    next_locked_resource = resource_metadata_collection.find_one(
        query, sort=[("unlock_date", 1)]
    )
    print(next_locked_resource, type(next_locked_resource))
    json_next = parse_json(next_locked_resource)
    if json_next:
        del json_next["_id"]
        return_list.append(json_next)
    return return_list


def get_resource_file(uuid: str) -> dict:
    query = {"uuid": uuid}
    results = db["resource_files"].find(query)
    for result in results:
        return result["file"]


def get_resource_metadata(uuid: str) -> dict:
    query = {"uuid": uuid}
    results = db["resource_metadata"].find(query)
    for result in results:
        return result


def get_resource_metadata_json(uuid: str) -> dict:
    query = {"uuid": uuid}
    result = db["resource_metadata"].find_one(query)
    json_res = parse_json(result)
    del json_res["_id"]

    return json_res


def update_resource_metadata(
    uuid: str, title: str, caption: str, uploaded_by: str, creation_date: date
):
    leave_date = date(day=13, month=11, year=2023)
    query = {"uuid": uuid}
    return db["resource_metadata"].update_one(
        query,
        update={
            "$set": {
                "title": title,
                "caption": caption,
                "uploaded_by": uploaded_by,
                "creation_date": creation_date.isoformat(),
                "unlock_date": calculate_unlock_date(
                    creation_date, leave_date
                ).isoformat(),
            }
        },
    )


def delete_image_by_uuid(uuid: str):
    query = {"uuid": uuid}
    db["resource_metadata"].delete_one(query)
    db["resource_files"].delete_one(query)
    print(f"Deleted image {uuid}", file=sys.stderr)


def parse_json(data):
    return json.loads(json_util.dumps(data))
