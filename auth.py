from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import time
import jwt
import os

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
tz = timezone(timedelta(hours=7))

class Auth:
    
    async def create_access_token(data: dict, expires_delta: timedelta):
        load_dotenv()
        SECRET_KEY = str(os.environ.get('SECRET_KEY'))
        to_encode = data.copy()
        expire = datetime.now(tz) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_jwt(token: str):
        load_dotenv()
        SECRET_KEY = str(os.environ.get('SECRET_KEY'))
        return jwt.decode(token, SECRET_KEY, ALGORITHM)

    async def verify_authen(token: str):
        try:
            payload = Auth.decode_jwt(token)
            if payload is None:
                raise HTTPException(status_code=401)
            if payload.get("exp") < int(time.time()):
                raise HTTPException(status_code=401, detail="Token is expired")
            return payload.get("id")
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Decoding error")
