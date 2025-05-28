from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

from src.validation.profile import validate_name, validate_gender, validate_birth_date


class ProfileCreateSchema(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str

    @validator("first_name", "last_name")
    def name_validator(cls, v):
        return validate_name(v)

    @validator("gender")
    def gender_validator(cls, v):
        return validate_gender(v)

    @validator("date_of_birth")
    def birth_date_validator(cls, v):
        return validate_birth_date(v)

    @validator("info")
    def info_validator(cls, v):
        if not v.strip():
            raise ValueError("Info cannot be empty or only spaces.")
        return v

class ProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: Optional[str]


