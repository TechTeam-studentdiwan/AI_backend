from fastapi import HTTPException
from openai import AsyncOpenAI
import os
from typing import List
from models import Message, Patient
from .openai import GET_PATIENT_DETAILS_FUNCTION, GET_PATIENT_DETAILS_BY_NAME_FUNCTION

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")



    async def get_patient_details(self, patient_id: str, hospital_id: str):
        patient_model = Patient()
        patient = await patient_model.get_patient(patient_id)
        if not patient or patient.get("hospital_id") != hospital_id:
            raise HTTPException(status_code=404, detail="Patient not found in this hospital.")
        # Optionally, filter out sensitive fields
        patient.pop("_id", None)
        return patient

    async def get_patient_details_by_name(self, name: str, hospital_id: str):
        patient_model = Patient()
        if patient_model.collection is None:
            await patient_model.init_collection()
        patient = await patient_model.collection.find_one({"name": name, "hospital_id": hospital_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found in this hospital.")
        patient.pop("_id", None)
        return patient


    async def generate_response(self, messages: List[Message], system_prompt: str = None):
        """Generate response from OpenAI, supporting patient detail function calls"""
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
                functions=[GET_PATIENT_DETAILS_FUNCTION, GET_PATIENT_DETAILS_BY_NAME_FUNCTION],
                function_call="auto",
                temperature=0.7,
                max_tokens=1000
            )
            message = response.choices[0].message
            if hasattr(message, "function_call") and message.function_call:
                fn = message.function_call
                if fn.name == "get_patient_details":
                    print("patient details function called")
                    import json
                    args = json.loads(fn.arguments)
                    return await self.get_patient_details(**args)
                elif fn.name == "get_patient_details_by_name":
                    import json
                    args = json.loads(fn.arguments)
                    return await self.get_patient_details_by_name(**args)
            return message.content
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
        except:
            return None