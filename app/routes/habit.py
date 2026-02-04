from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from app.database import get_db
from app.models.habit import Habit, HabitLog
from app.core.security import get_current_user
from app.models.user import User
from pydantic import BaseModel


router = APIRouter(prefix="/habits", tags=["Habits"])


# =========================
# SCHEMAS (LOCAL)
# =========================
class HabitCreate(BaseModel):
    name: str


class HabitResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class HabitLogResponse(BaseModel):
    habit_id: int
    date: date
    completed: bool
    sleep_hours: Optional[int] = None


class HabitToggle(BaseModel):
    date: Optional[date] = None
    sleep_hours: Optional[int] = None


# =========================
# CREATE HABIT
# =========================
@router.post("/", response_model=HabitResponse)
def create_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_habit = Habit(
        name=habit.name,
        user_id=current_user.id
    )

    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit


# =========================
# GET MY HABITS
# =========================
@router.get("/", response_model=List[HabitResponse])
def get_my_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id)
        .all()
    )


# =========================
# GET HABIT LOGS FOR MONTH
# =========================
@router.get("/logs", response_model=List[HabitLogResponse])
def get_habit_logs_for_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = date(year, month, 1)
    end = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )

    return (
        db.query(HabitLog)
        .join(Habit)
        .filter(
            Habit.user_id == current_user.id,
            HabitLog.date >= start,
            HabitLog.date < end
        )
        .all()
    )


# =========================
# TOGGLE HABIT FOR A DAY
# =========================
@router.post("/{habit_id}/toggle", response_model=HabitLogResponse)
def toggle_habit(
    habit_id: int,
    payload: HabitToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log_date = payload.date or date.today()

    habit = db.query(Habit).filter(Habit.id == habit_id).first()

    if not habit:
        raise HTTPException(404, "Habit not found")

    if habit.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    log = (
        db.query(HabitLog)
        .filter(
            HabitLog.habit_id == habit_id,
            HabitLog.user_id == current_user.id,
            HabitLog.date == log_date
        )
        .first()
    )

    if log:
        log.completed = not log.completed
    else:
        log = HabitLog(
            habit_id=habit_id,
            user_id = current_user.id,
            date=log_date,
            completed=True
        )
        db.add(log)

    # If sleep hours provided → auto mark completed
    if payload.sleep_hours is not None:
        log.sleep_hours = payload.sleep_hours
        log.completed = True

    db.commit()
    db.refresh(log)

    return {
        "habit_id": log.habit_id,
        "date": log.date,
        "completed": log.completed,
        "sleep_hours": log.sleep_hours
    }


# =========================
# DELETE HABIT
# =========================
@router.delete("/{habit_id}")
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()

    if not habit:
        raise HTTPException(404, "Habit not found")

    if habit.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    db.delete(habit)
    db.commit()
    return {"message": "Habit deleted"}
