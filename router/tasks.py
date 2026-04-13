from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Depends

from schemas import TaskCreate, TaskResponse, TaskUpdate
import models
from auth import CurrentUser

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def get_all_tasks(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' get all the tasks. DEVELOPER USE ONLY '''
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()

    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUser,  # if someone calls this endpoint without a valid token they get an Unathorized error even before function begins
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' create a task. user must be authenticated '''

    new_task = models.Task(
        title = task_data.title,
        description = task_data.description,
        completed = task_data.completed,
        user_id = current_user.id
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    task_id: int,
):
    ''' get info about a task. user must be authenticated '''

    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view this task")
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' update a task. user must be authenticated. '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this task")

    if task_data.title is not None and task_data.title != task.title:
        task.title = task_data.title

    if task_data.description is not None and task_data.description != task.description:
        task.description = task_data.description

    if task_data.completed is not None and task_data.completed != task.completed:
        task.completed = task_data.completed
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' delete a task. user must be authenticated '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this task")
    
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/complete", status_code=status.HTTP_202_ACCEPTED)
async def mark_task_completed(
    task_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' mark a task as completed. user must be authenticated '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this task")
    
    task.completed = True
    await db.commit()
    await db.refresh(task)

    return task


@router.post("/{task_id}/incomplete", status_code=status.HTTP_202_ACCEPTED)
async def mark_task_incomplete(
    task_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' mark a task as incomplete. user must be authenticated '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this task")

    task.completed = False
    await db.commit()
    await db.refresh(task)

    return task


@router.get("/users/{user_id}", response_model=list[TaskResponse])
async def get_users_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    current_user: CurrentUser,
    limit: int = 10,
    offset: int = 0,
    completed: bool | None = None,
):
    ''' get all the tasks of a user. user must be authenticated. limit, offset, completed. '''
    
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view this user's tasks")

    result = await db.execute(
        select(models.Task).where(models.Task.user_id == user_id)
    )
    
    if completed is not None:
        result = result.where(models.Task.completed == completed)

    result = result.limit(limit).offset(offset)
    tasks = result.scalars().all()

    return tasks