from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 👤 Basic Info
    name = Column(String, nullable=False)

    # 📧 Email Auth
    email = Column(String, unique=True, index=True, nullable=True)
    email_verified = Column(Boolean, default=False)

    # 📱 Phone Auth
    phone_number = Column(String, unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False)

    # 🔐 Password (optional now)
    hashed_password = Column(String, nullable=True)

    # 🔑 Auth provider
    # email | phone | google
    auth_provider = Column(String, nullable=False, default="email")

    # 🟢 Google OAuth
    google_id = Column(String, unique=True, index=True, nullable=True)

    # 🧑‍⚖️ Role
    role = Column(String, default="user")

    # 🔗 Tasks relationship
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete"
    )

    # 🔗 Refresh tokens
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete"
    )

