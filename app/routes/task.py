from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Optional

from app.database import get_db
from app.models.task import Task
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskListResponse,
)
from app.core.security import get_current_user,require_admin
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# =========================
# CREATE TASK
# =========================
@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_task = Task(
        title=task.title,
        description=task.description,
        user_id=current_user.id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# =========================
# GET MY TASKS (PAGINATION + FILTER)
# =========================
@router.get("/", response_model=TaskListResponse)
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    completed: Optional[bool] = None,
    search: Optional[str] = None,
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if completed is not None:
        query = query.filter(Task.completed == completed)

    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    offset = (page - 1) * limit

    tasks = (
        query.order_by(desc(Task.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "tasks": tasks,
    }


# =========================
# UPDATE TASK
# =========================
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task",
        )

    if task_data.title is not None:
        task.title = task_data.title

    if task_data.description is not None:
        task.description = task_data.description

    if task_data.completed is not None:
        task.completed = task_data.completed

    db.commit()
    db.refresh(task)
    return task


# =========================
# DELETE TASK
# =========================
@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task",
        )

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@router.get("/admin/all", response_model=TaskListResponse)
def get_all_tasks_admin(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
    page: int = 1,
    limit: int = 10,
):
    query = db.query(Task)
    total = query.count()
    offset = (page - 1) * limit

    tasks = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "tasks": tasks,
    }
