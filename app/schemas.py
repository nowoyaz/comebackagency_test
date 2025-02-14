# app/schemas.py
from typing import List, Optional
from pydantic import BaseModel, conint, validator
from datetime import datetime

ALLOWED_GENRES = {"Fiction", "Non-Fiction", "Science", "History"}

class AuthorBase(BaseModel):
    name: str

    @validator("name")
    def non_empty_name(cls, v):
        if not v.strip():
            raise ValueError("Author name must be a non-empty string")
        return v

class AuthorCreate(AuthorBase):
    pass

class AuthorOut(AuthorBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True

class BookBase(BaseModel):
    title: str
    genre: str
    published_year: int

    @validator("title")
    def non_empty_title(cls, v):
        if not v.strip():
            raise ValueError("Title must be a non-empty string")
        return v

    @validator("genre")
    def validate_genre(cls, v):
        if v not in ALLOWED_GENRES:
            raise ValueError(f"Genre must be one of {ALLOWED_GENRES}")
        return v

    @validator("published_year")
    def validate_published_year(cls, v):
        current_year = datetime.now().year
        if v < 1800 or v > current_year:
            raise ValueError(f"Published year must be between 1800 and {current_year}")
        return v

class BookCreate(BookBase):
    authors: List[str]  # список имён авторов

    @validator("authors", each_item=True)
    def non_empty_author(cls, v):
        if not v.strip():
            raise ValueError("Author name must be a non-empty string")
        return v

class BookUpdate(BaseModel):
    title: Optional[str]
    genre: Optional[str]
    published_year: Optional[int]
    authors: Optional[List[str]]

    @validator("title")
    def non_empty_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title must be a non-empty string")
        return v

    @validator("genre")
    def validate_genre(cls, v):
        if v is not None and v not in ALLOWED_GENRES:
            raise ValueError(f"Genre must be one of {ALLOWED_GENRES}")
        return v

    @validator("published_year")
    def validate_published_year(cls, v):
        if v is not None:
            current_year = datetime.now().year
            if v < 1800 or v > current_year:
                raise ValueError(f"Published year must be between 1800 and {current_year}")
        return v

    @validator("authors", each_item=True)
    def non_empty_author(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Author name must be a non-empty string")
        return v

class BookOut(BookBase):
    id: int
    authors: List[AuthorOut]

    class Config:
        orm_mode = True
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_admin: bool

    class Config:
        orm_mode = True
        from_attributes = True

class UserLogin(UserBase):
    password: str
