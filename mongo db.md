# MongoDB Conversation Management System with FastAPI

## 1. MongoDB Schema Design

```python
# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class Conversation(BaseModel):
    conversation_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True

# Request/Response Models
class StartConversationRequest(BaseModel):
    user_id: Optional[str] = None
    initial_message: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StartConversationResponse(BaseModel):
    conversation_id: str
    created_at: datetime

class AddMessageRequest(BaseModel):
    message: str
    metadata: Optional[Dict[str, Any]] = None

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
```

## 2. Database Connection and Operations

```python
# database.py
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
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
```

## 3. OpenAI Integration Service

```python
# openai_service.py
from openai import AsyncOpenAI
import os
from typing import List
from models import Message, MessageRole

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def generate_response(self, messages: List[Message], system_prompt: str = None):
        """Generate response from OpenAI"""
        # Convert our Message objects to OpenAI format
        openai_messages = []
        
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in messages:
            openai_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_conversation_title(self, messages: List[Message]):
        """Generate a title for the conversation based on initial messages"""
        if len(messages) < 2:
            return None
            
        prompt = f"Generate a short, descriptive title (max 50 chars) for this conversation:\n"
        prompt += f"User: {messages[0].content[:200]}...\n"
        prompt += f"Assistant: {messages[1].content[:200]}..."
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a concise title for the conversation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=20
            )
            
            return response.choices[0].message.content.strip('"').strip()
        except:
            return None
```

## 4. FastAPI Application

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from datetime import datetime
from typing import Optional

from models import *
from database import *
from openai_service import OpenAIService

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI service
openai_service = OpenAIService()

@app.post("/api/conversations/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Start a new conversation"""
    try:
        # Generate unique conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Initialize messages list
        messages = []
        
        # Add system message if provided
        if request.system_prompt:
            messages.append(Message(
                role=MessageRole.SYSTEM,
                content=request.system_prompt
            ))
        
        # Add initial user message if provided
        if request.initial_message:
            messages.append(Message(
                role=MessageRole.USER,
                content=request.initial_message
            ))
        
        # Create conversation object
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=request.user_id,
            messages=messages,
            metadata=request.metadata
        )
        
        # Save to MongoDB
        await create_conversation(conversation)
        
        # If initial message provided, generate AI response
        if request.initial_message:
            ai_response = await openai_service.generate_response(
                messages,
                request.system_prompt
            )
            
            # Add AI response to conversation
            ai_message = Message(
                role=MessageRole.ASSISTANT,
                content=ai_response
            )
            await add_message_to_conversation(conversation_id, ai_message)
            
            # Generate title after first exchange
            if len(messages) >= 1:
                title = await openai_service.generate_conversation_title(
                    messages + [ai_message]
                )
                if title:
                    await update_conversation(conversation_id, {"title": title})
        
        return StartConversationResponse(
            conversation_id=conversation_id,
            created_at=conversation.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str):
    """Get all messages from a conversation"""
    try:
        conversation = await get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationHistoryResponse(
            conversation_id=conversation["conversation_id"],
            messages=[Message(**msg) for msg in conversation["messages"]],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            title=conversation.get("title")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, request: AddMessageRequest):
    """Add a user message and get AI response"""
    try:
        # Get existing conversation
        conversation = await get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.message,
            metadata=request.metadata
        )
        await add_message_to_conversation(conversation_id, user_message)
        
        # Get all messages for context
        all_messages = [Message(**msg) for msg in conversation["messages"]]
        all_messages.append(user_message)
        
        # Get system prompt if exists
        system_prompt = None
        if all_messages and all_messages[0].role == MessageRole.SYSTEM:
            system_prompt = all_messages[0].content
            # Remove system message from the list for OpenAI
            all_messages = all_messages[1:]
        
        # Generate AI response
        ai_response = await openai_service.generate_response(
            all_messages,
            system_prompt
        )
        
        # Add AI response to conversation
        ai_message = Message(
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        await add_message_to_conversation(conversation_id, ai_message)
        
        # Update title if not set and we have enough messages
        if not conversation.get("title") and len(all_messages) >= 2:
            title = await openai_service.generate_conversation_title(all_messages)
            if title:
                await update_conversation(conversation_id, {"title": title})
        
        return {
            "user_message": user_message.dict(),
            "ai_response": ai_message.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/conversations")
async def get_user_conversations_list(user_id: str, limit: int = 20):
    """Get all conversations for a user"""
    try:
        conversations = await get_user_conversations(user_id, limit)
        
        # Format response
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "conversation_id": conv["conversation_id"],
                "title": conv.get("title", "Untitled Conversation"),
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "message_count": len(conv.get("messages", []))
            })
        
        return {"conversations": formatted_conversations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Soft delete a conversation"""
    try:
        result = await update_conversation(
            conversation_id,
            {"is_active": False, "updated_at": datetime.utcnow()}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 5. Environment Variables (.env)

```bash
# .env
MONGODB_URL=mongodb://localhost:27017
DB_NAME=conversation_db
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

## 6. Requirements.txt

```txt
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
pymongo==4.6.0
pydantic==2.5.0
openai==1.6.1
python-dotenv==1.0.0
```

## 7. Usage Examples

```python
# client_example.py
import httpx
import asyncio

async def example_usage():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Start a new conversation
        start_response = await client.post(
            f"{base_url}/api/conversations/start",
            json={
                "user_id": "user123",
                "initial_message": "What is machine learning?",
                "system_prompt": "You are a helpful AI assistant."
            }
        )
        conversation_data = start_response.json()
        conversation_id = conversation_data["conversation_id"]
        print(f"Started conversation: {conversation_id}")
        
        # 2. Get conversation history
        history_response = await client.get(
            f"{base_url}/api/conversations/{conversation_id}"
        )
        history = history_response.json()
        print(f"Messages: {len(history['messages'])}")
        
        # 3. Add more messages
        add_message_response = await client.post(
            f"{base_url}/api/conversations/{conversation_id}/messages",
            json={
                "message": "Can you give me a practical example?"
            }
        )
        print("Added message and got response")
        
        # 4. Get user's conversations
        user_conversations = await client.get(
            f"{base_url}/api/users/user123/conversations"
        )
        print(f"User has {len(user_conversations.json()['conversations'])} conversations")

if __name__ == "__main__":
    asyncio.run(example_usage())
```

## 8. MongoDB Indexes (for performance)

```javascript
// Run these in MongoDB shell for better performance
db.conversations.createIndex({ "conversation_id": 1 })
db.conversations.createIndex({ "user_id": 1, "updated_at": -1 })
db.conversations.createIndex({ "created_at": -1 })
```