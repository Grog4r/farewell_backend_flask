from datetime import date
from uuid import UUID, uuid1

import bson
from bson.binary import Binary
from werkzeug.datastructures import FileStorage

from utils import calculate_unlock_date


class ResourceMetadata:
    def __init__(self, file_name: str, creation_date: date, caption: str, uploaded_by: str):
        self.uuid = uuid1()
        self.file_name = file_name
        self.creation_date = creation_date
        leave_date = date(day=13, month=11, year=2023)
        self.unlock_date = calculate_unlock_date(creation_date, leave_date)
        self.caption = caption
        self.uploaded_by = uploaded_by

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "file_name": self.file_name,
            "creation_date": self.creation_date.isoformat(),
            "unlock_date": self.unlock_date.isoformat(),
            "caption": self.caption,
            "uploaded_by": self.uploaded_by,
        }


class ResourceFile:
    def __init__(self, uuid: UUID, file: FileStorage):
        self.uuid = uuid
        self.file = file

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "file": Binary(self.file.stream.read()),
        }
