from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# =========================
# HABIT
# =========================

class HabitCreate(BaseModel):
    name: str = Field(min_length=1)


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)


class HabitResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class HabitListResponse(BaseModel):
    total: int
    habits: List[HabitResponse]


# =========================
# HABIT LOG (daily check)
# =========================

class HabitLogCreate(BaseModel):
    day: date
    completed: bool


class HabitLogResponse(BaseModel):
    id: int
    day: date
    completed: bool

    class Config:
        from_attributes = True
