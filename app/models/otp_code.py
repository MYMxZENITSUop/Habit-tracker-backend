from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from datetime import datetime, timedelta

from app.database import Base


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)

    # 📧 email OR 📱 phone number
    identifier = Column(String, index=True, nullable=False)

    # 🔐 Hashed OTP (never store plain OTP)
    otp_hash = Column(String, nullable=False)

    # ⏰ Expiry time
    expires_at = Column(DateTime, nullable=False)

    # ✅ Mark OTP as used
    verified = Column(Boolean, default=False)

    # 🕒 Created time
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_identifier_verified", "identifier", "verified"),
    )

    @staticmethod
    def expiry_time(minutes: int = 5):
        return datetime.utcnow() + timedelta(minutes=minutes)
