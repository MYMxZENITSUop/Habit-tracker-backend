from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.otp_code import OTPCode
from app.models.user import User
from app.schemas.user import TokenResponse
from app.core.security import create_access_token, create_refresh_token

from app.utils.email import send_otp_email
from app.utils.otp import generate_otp, hash_otp, verify_otp

router = APIRouter(prefix="/auth/email", tags=["Auth - Email OTP"])


# =========================
# SEND EMAIL OTP
# =========================
@router.post("/send-otp")
def send_email_otp_route(email: str, db: Session = Depends(get_db)):
    otp = generate_otp()

    otp_entry = OTPCode(
        identifier=email,
        otp_hash=hash_otp(otp),
        expires_at=OTPCode.expiry_time(),
    )

    db.add(otp_entry)
    db.commit()

    send_otp_email(email, otp)

    return {"message": "OTP sent to email"}


# =========================
# VERIFY EMAIL OTP
# =========================
@router.post("/verify-otp", response_model=TokenResponse)
def verify_email_otp_route(
    email: str,
    otp: str,
    db: Session = Depends(get_db),
):
    otp_entry = (
        db.query(OTPCode)
        .filter(
            OTPCode.identifier == email,
            OTPCode.verified == False,
            OTPCode.expires_at > datetime.utcnow(),
        )
        .order_by(OTPCode.created_at.desc())
        .first()
    )

    if not otp_entry or not verify_otp(otp, otp_entry.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    otp_entry.verified = True

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=email.split("@")[0],
            email=email,
            email_verified=True,
            auth_provider="email",
        )
        db.add(user)

    user.email_verified = True
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
