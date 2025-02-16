from fastapi import FastAPI
from nicegui import ui
from app.auth.routes import router as auth_router
from app.db import engine, Base
from app.ui.pages.login import login_page
from app.ui.pages.signup import signup_page
from app.ui.pages.calendar import calendar_page
from fastapi.staticfiles import StaticFiles

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Include authentication routes
app.include_router(auth_router, prefix="/api/auth")

# Register pages
login_page()
signup_page()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Run NiceGUI with FastAPI
ui.run_with(app, title="Meetly")
