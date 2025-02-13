from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime

class TokenType(str, Enum):
    FREE = "free"
    PAID = "paid"

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None

class User(BaseModel):
    username: str
    email: EmailStr = None
    full_name: str = None
    disabled: bool = None

class UserInDB(User):
    hashed_password: str

# User registration model
class UserCreate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str

class token_data(BaseModel):
    token:str
    expiry:datetime