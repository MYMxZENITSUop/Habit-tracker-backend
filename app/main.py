import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import user, task, refresh_token

from app.routes.user import router as user_router
from app.routes.task import router as task_router
from app.routes.auth_email import router as email_auth_router
from app.routes.auth_phone import router as auth_phone_router

# =========================
# APP INIT (MUST BE FIRST)
# =========================
app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STARTUP EVENT
# =========================
@app.on_event("startup")
def startup_event():
    retries = 10
    while retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database connected")
            break
        except Exception:
            print("⏳ Waiting for database...")
            retries -= 1
            time.sleep(2)

# =========================
# ROUTERS (AFTER app init)
# =========================
app.include_router(user_router)
app.include_router(task_router)
app.include_router(email_auth_router)
app.include_router(auth_phone_router)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "message": "Task Manager Backend with FastAPI & PostgreSQL is running"
    }
