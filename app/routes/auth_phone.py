from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse
from app.core.security import create_access_token, create_refresh_token

from firebase_admin import auth as firebase_auth

router = APIRouter(prefix="/auth/phone", tags=["Auth - Phone OTP"])


@router.post("/verify", response_model=TokenResponse)
def verify_phone_otp(
    firebase_token: str,
    db: Session = Depends(get_db),
):
    try:
        decoded = firebase_auth.verify_id_token(firebase_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    phone = decoded.get("phone_number")

    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number not found in token",
        )

    user = db.query(User).filter(User.phone_number == phone).first()

    if not user:
        user = User(
            name=phone,
            phone_number=phone,
            phone_verified=True,
            auth_provider="phone",
        )
        db.add(user)

    user.phone_verified = True
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": phone})
    refresh_token = create_refresh_token({"sub": phone})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
