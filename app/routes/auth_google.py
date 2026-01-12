from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import (
    create_access_token,
    create_refresh_token,
)
from datetime import datetime, timedelta
from app.core.security import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/auth", tags=["Auth - Google"])


@router.post("/google")
def google_auth(
    firebase_token: dict,
    db: Session = Depends(get_db),
):
    """
    Expects:
    {
      "firebase_token": "<ID_TOKEN>"
    }
    """

    try:
        decoded_token = firebase_auth.verify_id_token(
            firebase_token["firebase_token"]
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

    # 🔍 Check if user exists
    user = db.query(User).filter(User.email == email).first()

    # 🆕 Create user if first-time Google login
    if not user:
        user = User(
            name=name,
            email=email,
            hashed_password="",  # no password for Google users
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 🔐 Create JWT tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    # 💾 Store refresh token
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
