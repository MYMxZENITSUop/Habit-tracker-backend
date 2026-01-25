from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List
from datetime import timedelta, datetime

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    TokenResponse,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    require_admin,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

router = APIRouter(prefix="/users", tags=["Users"])


# =========================
# CREATE USER
# =========================
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user.name,
        email=user.email.lower(),
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# =========================
# BULK CREATE USERS
# =========================
@router.post("/bulk", response_model=List[UserResponse])
def create_users_bulk(users: List[UserCreate], db: Session = Depends(get_db)):
    created_users = []

    for user in users:
        if db.query(User).filter(User.email == user.email).first():
            continue

        new_user = User(
            name=user.name,
            email=user.email.lower(),
            hashed_password=hash_password(user.password),
        )
        db.add(new_user)
        created_users.append(new_user)

    db.commit()
    for u in created_users:
        db.refresh(u)

    return created_users


# =========================
# LOGIN
# =========================
@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # revoke old refresh tokens (optional but professional)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})

    access_token = create_access_token(
    data={"sub": str(user.id)},
    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
    data={"sub": str(user.id)}
    )

    db_refresh_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(db_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# =========================
# REFRESH ACCESS TOKEN
# =========================

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    refresh_token = payload.refresh_token

    payload_data = verify_refresh_token(refresh_token)

    token_entry = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False,
        )
        .first()
    )

    if not token_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    new_access_token = create_access_token(
        data={"sub": payload_data["sub"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# =========================
# LOGOUT
# =========================
class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    refresh_token = payload.refresh_token

    token_entry = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == refresh_token)
        .first()
    )

    if not token_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_entry.revoked = True
    db.commit()

    return {"message": "Logged out successfully"}


# =========================
# GET CURRENT USER
# =========================
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# =========================
# GET USERS (PAGINATION + SEARCH)
# =========================
@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = None,
):
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    return query.offset(offset).limit(limit).all()


# =========================
# GET USER BY ID
# =========================
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# =========================
# UPDATE USER
# =========================
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email:
        exists = (
            db.query(User)
            .filter(User.email == user_data.email, User.id != user_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Email already exists")

    if user_data.name is not None:
        user.name = user_data.name

    if user_data.email is not None:
        user.email = user_data.email.lower()

    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)

    db.commit()
    db.refresh(user)
    return user


# =========================
# DELETE USER
# =========================
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted by admin"}

@router.get("/admin/all-users", response_model=List[UserResponse])
def get_all_users_admin(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return db.query(User).all()