from openai import AsyncOpenAI
import os
from typing import List
from models import Message
from fastapi import Depends, HTTPException
from core.database import get_db
from models.patient import Patient

# OpenAI function schema for getting patient details
GET_PATIENT_DETAILS_FUNCTION = {
    "name": "get_patient_details",
    "description": "Get patient details from hospital in real time.",
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string", "description": "The unique patient ID."},
            "hospital_id": {"type": "string", "description": "The hospital's unique ID."}
        },
        "required": ["patient_id", "hospital_id"]
    }
}

GET_PATIENT_DETAILS_BY_NAME_FUNCTION = {
    "name": "get_patient_details_by_name",
    "description": "Get patient details from hospital in real time using patient name and hospital ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The patient's name."},
            "hospital_id": {"type": "string", "description": "The hospital's unique ID."}
        },
        "required": ["name", "hospital_id"]
    }
}

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

    async def generate_response(self, messages: List[Message], system_prompt=
            """You are a helpful assistant. Respond briefly, clearly, and only with directly relevant facts.
            Avoid extra details unless the user asks explicitly. 
            If the user asks a general question, give only a short factual answer. 
            If the user requests more info (e.g., room number, appointment time), respond accordingly. 
            Do not guess, assume, or invent information."""
        ):
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
            error_message = str(e)
            if "invalid_api_key" in error_message.lower():
                raise Exception("Invalid OpenAI API key. Please check your API key in the .env file.")
            elif "insufficient_quota" in error_message.lower():
                raise Exception("OpenAI API quota exceeded. Please check your account balance.")
            elif "rate limit" in error_message.lower():
                raise Exception("OpenAI API rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"OpenAI API error: {error_message}")

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
        except Exception as e:
            error_message = str(e)
            if "invalid_api_key" in error_message.lower():
                print("Warning: Invalid OpenAI API key when generating conversation title.")
            elif "insufficient_quota" in error_message.lower():
                print("Warning: OpenAI API quota exceeded when generating conversation title.")
            elif "rate limit" in error_message.lower():
                print("Warning: OpenAI API rate limit exceeded when generating conversation title.")
            else:
                print(f"Warning: OpenAI API error when generating conversation title: {error_message}")
            return None

    # Example: integrate function call into chat logic (pseudo-code)
    # async def chat_with_functions(self, ...):
    #     ...
    #     functions=[GET_PATIENT_DETAILS_FUNCTION, GET_PATIENT_DETAILS_BY_NAME_FUNCTION]
    #     ...
    #     if function_call.name == "get_patient_details":
    #         return await self.get_patient_details(**function_call.arguments)
    #     elif function_call.name == "get_patient_details_by_name":
    #         return await self.get_patient_details_by_name(**function_call.arguments)
    #     ...
