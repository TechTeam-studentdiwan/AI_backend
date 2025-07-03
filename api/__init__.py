from fastapi import FastAPI
from main import app as main_app
from core.database import get_db

# Use the app from main.py in the root
app = main_app