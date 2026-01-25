from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import (
    create_access_token,
    create_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

router = APIRouter(prefix="/auth", tags=["Auth - Google"])


class GoogleAuthRequest(BaseModel):
    firebase_token: str


@router.post("/google")
def google_auth(
    payload: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    try:
        decoded_token = firebase_auth.verify_id_token(
            payload.firebase_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    email = decoded_token.get("email")
    name = decoded_token.get("name") or "Google User"

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not available from Google",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            hashed_password="",
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # ✅ FIXED: use user.id in JWT
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    db_refresh = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow()
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(db_refresh)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
