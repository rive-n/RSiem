from pydantic import BaseModel, validator, ValidationError
from fastapi import UploadFile
from typing import Optional, List


class FileModel(BaseModel):
    files: List[UploadFile]
    serviceName: str
    description: Optional[str] = None

    @validator('filename', check_fields=False)
    def validate_filename(cls, value):
        for file in value:
            if ".." in file or "/" in file or "\\" in file or any([(ord(sym) <= 32 or ord(sym) > 127) for sym in file]):
                raise ValidationError("Value must not contain bad symbols")
        return value

    @validator('serviceName', check_fields=False)
    def validate_serviceName(cls, value):
        if ".." not in value and "/" not in value and "\\" not in value and any([(32 < ord(sym) < 127) for sym in value]):
            return value
        raise ValidationError("Value must not contain bad symbols")