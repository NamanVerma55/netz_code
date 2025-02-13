from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

DB_CONFIG = {
    "host": "",
    "dbname": "",
    "user": "",
    "password": "",
    "port": ""
}

Secret_key = "e1b0728868df0738484eb7a6e23f8638"
algorithm = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context= CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")