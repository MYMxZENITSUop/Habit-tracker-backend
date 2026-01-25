import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import habit, user, refresh_token

from app.core.firebase import init_firebase
from app.routes.user import router as user_router
from app.routes.habit import router as habit_router
from app.routes.auth_email import router as email_auth_router
from app.routes.auth_phone import router as auth_phone_router
from app.routes.auth_google import router as google_auth_router


app = FastAPI(
    title="HABIT TRACKER API",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    init_firebase()

    retries = 10
    while retries:
        try:
            # TEMP: OK for now, later replaced by Alembic
            Base.metadata.create_all(bind=engine)
            print("✅ Database connected")
            break
        except Exception:
            print("⏳ Waiting for database...")
            retries -= 1
            time.sleep(2)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(user_router)
app.include_router(habit_router)
app.include_router(email_auth_router)
app.include_router(auth_phone_router)
app.include_router(google_auth_router)

@app.get("/")
def root():
    return {
        "message": "Habit Tracker Backend with FastAPI & PostgreSQL is running"
    }
