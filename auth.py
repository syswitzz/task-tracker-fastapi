import jwt
from typing import Annotated
from pwdlib import PasswordHash
from datetime import timedelta, datetime, UTC

import models
from config import settings
from database import get_db

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer



# uv add "pwdlib[argon2]" pydantic-settings pyjwt

# Why hashing and not encryption?
# Encryption is reversible, Hashing is not. even if db is stolen password can be recovered from hashes
# argon2 generates random salt for same password. each is unique. 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")  # token url has to match login endpoint path
password_hasher = PasswordHash.recommended()



def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:  # data = {"sub": str(user.id)}
    ''' Create a JWT access token. '''

    # in case expiry time is None

    if expires_delta:
        expires = datetime.now(UTC) + expires_delta
    else:
        expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = data.copy()
    to_encode.update({"exp": expires})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    ''' Verifies a JWT token and returns the user id if it is valid '''

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]}   
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> models.User:
    '''Any route that uses this Dependency will automatically require a valid token and get access to the full User object'''

    user_id = verify_access_token(token=token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try: 
        user_id = int(user_id)  # this is incase JWT throws some error. its better to catch it here than in verify_access_token func
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


# Annotated - is for typehinting it tells that "CurrentUser" is a "models.User" object
# Depends - and the metadata for the "models.User" depends on "get_current_user" 

CurrentUser = Annotated[models.User, Depends(get_current_user)]
    
