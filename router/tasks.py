from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Depends

from schemas import TaskCreate, TaskResponse, TaskUpdate
import models

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def get_all_tasks(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' get all the tasks '''
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()

    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' create a task '''
    # check if user exists
    result = await db.execute(
        select(models.User).where(models.User.id == task_data.user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_task = models.Task(
        title = task_data.title,
        description = task_data.description,
        completed = task_data.completed,
        user_id = task_data.user_id
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task



@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: int,
):
    ''' get info about a task '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ''' update a task '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task_data.title is not None and task_data.title != task.title:
        task.title = task_data.title

    if task_data.description is not None and task_data.description != task.description:
        task.description = task_data.description

    if task_data.completed is not None and task_data.completed != task_data.completed:
        task.completed = task_data.completed
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ''' delete a task '''
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    await db.delete(task)
    await db.commit()


@router.get("/users/{user_id}", response_model=list[TaskResponse])
async def get_users_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
):
    ''' get all the tasks of a user '''

    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(
        select(models.Task).where(models.Task.user_id == user_id)
    )
    tasks = result.scalars().all()

    return tasks


