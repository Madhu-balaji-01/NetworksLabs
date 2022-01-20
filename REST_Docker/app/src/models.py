from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    first_name: str
    last_name: str
    role: str
    gpa: Optional[float]
    created_at: Optional[str] = None
    password: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "role": "student",
                "gpa": 3.5,
                "created_at": "datetime",
                "password": "fakepassword",
            }
        }


class UpdateUserModel(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[str]
    gpa: Optional[float]
    created_at: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "role": "student",
                "gpa": 3.5,
                "created_at": "datetime"
            }
        }


class ShowUserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[str]
    gpa: Optional[float]
    created_at: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "role": "student",
                "gpa": 3.5,
                "created_at": "datetime"
            }
        }
