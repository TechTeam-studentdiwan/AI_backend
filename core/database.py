import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from models import Conversation, Message
from datetime import datetime

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    mongodb_url = "mongodb+srv://rc:iZm5uSPh0ZnpLlgH@cluster0.ekb8qkv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    if not mongodb_url:
        raise ValueError("MONGODB_URL environment variable is not set")

    db.client = AsyncIOMotorClient(mongodb_url)
    db.database = db.client[os.getenv("DB_NAME", "conversation_db")]

async def close_mongo_connection():
    if db.client:
        db.client.close()

# Conversation operations
async def create_conversation(conversation: Conversation):
    """Create a new conversation in MongoDB"""
    result = await db.database.conversations.insert_one(
        conversation.dict()
    )
    return str(result.inserted_id)

async def get_conversation(conversation_id: str):
    """Retrieve conversation by ID"""
    conversation = await db.database.conversations.find_one(
        {"conversation_id": conversation_id}
    )
    return conversation

async def update_conversation(conversation_id: str, update_data: dict):
    """Update conversation"""
    result = await db.database.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def add_message_to_conversation(conversation_id: str, message: Message):
    """Add a message to existing conversation"""
    result = await db.database.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {"messages": message.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    return result.modified_count > 0

async def get_user_conversations(user_id: str, limit: int = 20):
    """Get all conversations for a user"""
    cursor = db.database.conversations.find(
        {"user_id": user_id, "is_active": True}
    ).sort("updated_at", -1).limit(limit)

    conversations = []
    async for conv in cursor:
        conversations.append(conv)
    return conversations