from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import random
from datetime import datetime
from typing import Optional

from models import *
from core.database import *
from services import OpenAIService

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

@app.get("/hh")
async def hello():
    return {"hello":"world"}

@app.post("/api/conversations/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Start a new conversation"""
    try:
        # Generate unique conversation ID in the format CHAT-{random_string}-{timestamp}
        random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        conversation_id = f"chat-{random_string}-{timestamp}"

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
