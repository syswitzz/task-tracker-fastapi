from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, SecretStr


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120) # no min length req., as EmailStr already validates the email

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # allows us to create a UserResponse from a User model instance without manually converting it to a dict first
    
    id: int


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=200)
    completed: bool = False
    user_id: int

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=200)
    completed: bool | None = None

class TaskResponse(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_created: datetime
    
