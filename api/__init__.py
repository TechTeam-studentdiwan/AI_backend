from fastapi import FastAPI
from app.main import app as main_app
from core.database import get_db

# Use the app from app/main.py
app = main_app