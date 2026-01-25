from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    owner = relationship("User", back_populates="habits")
    logs = relationship(
        "HabitLog",
        back_populates="habit",
        cascade="all, delete"
    )


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, default=False)
    sleep_hours = Column(Integer, nullable=True)

    habit_id = Column(
        Integer,
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    habit = relationship("Habit", back_populates="logs")

    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="unique_habit_day"),
        Index("idx_habit_month", "habit_id", "date"),
    )
