"""backend/main.py

Main FastAPI application entry point for BuyLater.
Configures CORS, static files, database initialization, default user seeding,
and router registration.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import engine, Base, SessionLocal
from backend.models import User
from backend.utils.security import hash_password
from backend.routers import (
    users,
    products,
    my_stuff,
    purchases,
    analysis,
    feedback,
    dashboard,
)


def seed_demo_user():
    """Seeds a friendly default demo user if the database is brand new."""
    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if not existing_user:
            demo_user = User(
                name="Sindhu",
                email="demo@buylater.app",
                password_hash=hash_password("password123"),
                monthly_budget=25000.0,
                personality="Best Friend",
            )
            db.add(demo_user)
            db.commit()
            print("Seeded demo user: Sindhu (demo@buylater.app / ID: 1)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist & demo user is seeded
    Base.metadata.create_all(bind=engine)
    seed_demo_user()
    yield


app = FastAPI(
    title="BuyLater API",
    description="Personal Spending-Behavior Assistant — 'Do I Actually Need This?'",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Mount Frontend directory so pages can be accessed directly from http://localhost:8000/
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Include API Routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(my_stuff.router)
app.include_router(purchases.router)
app.include_router(analysis.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {
        "project": "BuyLater",
        "tagline": "Do I Actually Need This?",
        "status": "online",
        "docs": "/docs",
        "app_ui": "/app/index.html",
    }
