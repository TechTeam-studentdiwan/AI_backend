from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.database import db
import base64
import tempfile

from services import OpenAIService

router = APIRouter()

class VectorStoreFileRequest(BaseModel):
    name: str = "default-store"
    filename: str = "file.txt"  # Default filename if not provided
    file_data: str  # base64-encoded file content


