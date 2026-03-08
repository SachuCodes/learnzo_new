from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(
    # bcrypt has a 72-byte password limit; bcrypt_sha256 avoids this by pre-hashing.
    # Keep bcrypt for backward compatibility with any existing stored hashes.
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)



# ---------- PASSWORDS -------
def get_hashed_password(password: str) -> str:
    # Guard against extremely large inputs; bcrypt_sha256 supports long passwords,
    # but we still cap to a reasonable size to avoid abuse.
    if len(password.encode("utf-8")) > 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long"
        )
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- TOKENS ----------

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES or 60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
