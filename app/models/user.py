from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    role = Column(String, default="user")  # "user" | "admin"


    # 🔗 tasks relationship (THIS WAS MISSING)
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete"
    )

    # 🔗 refresh tokens relationship
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete"
    )
