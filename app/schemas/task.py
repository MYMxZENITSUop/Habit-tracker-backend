from pydantic import BaseModel, Field
from typing import Optional, List


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    completed: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int
    page: int
    limit: int
    tasks: List[TaskResponse]
