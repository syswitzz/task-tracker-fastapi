from typing import Annotated
from datetime import timedelta, UTC

from fastapi import APIRouter, APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from schemas import UserCreate, UserResponse, UserUpdate, Token
import models
from config import settings
from auth import hash_password, verify_password, create_access_token

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' get all the users '''
    result = await db.execute(select(models.User))
    users = result.scalars().all()

    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' create a user '''
    # check for existing email
    result = await db.execute(
        select(models.User).where(models.User.email == user_data.email.lower())
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = models.User(
        username = user_data.username,
        email = user_data.email.lower(),
        password_hash = hash_password(user_data.password),
    )

    db.add(new_user)    # we dont use await here because it just adds the object to to session pending list. it doesnt do any I/O
    await db.commit()   # executes and saves to the db
    await db.refresh(new_user)  # reloads the object from db

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int
):
    ''' get info about a user '''
    # check if user exists
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' update a user '''
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    
    if user_data.email is not None and user_data.email.lower() != user.email:
        # check for existing email
        result = await db.execute(
            select(models.User)
                .where(models.User.email == user_data.email.lower())
            )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        user.email = user_data.email.lower()    # directly changed to db model

    if user_data.password is not None and not verify_password(user_data.password, user.password_hash):
        user.password_hash = hash_password(user_data.password)
    
    if user_data.username is not None and user_data.username != user.username:
        user.username = user_data.username

    await db.commit()
    await db.refresh(user)
    return user
    

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' delete a user '''
    result = await db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' returns token. we have 1. form_data.password, form_data.username'''
    # OAuth2PasswordRequestForm uses "username" field, but treat is as email

    result = await db.execute(select(models.User).where(models.User.email == form_data.username.lower()))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # create the temporary access token if credentials are correct
    access_token = create_access_token(
        data = {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return Token(token_type="bearer", access_token=access_token)