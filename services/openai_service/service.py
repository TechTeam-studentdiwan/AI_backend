import os
from typing import List
from fastapi import HTTPException
from openai import AsyncOpenAI
from models import Message
from .function_calls import get_patient_details, get_patient_details_by_name, GET_PATIENT_DETAILS_FUNCTION, GET_PATIENT_DETAILS_BY_NAME_FUNCTION

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    async def generate_response(self, messages: List[Message], system_prompt: str = None):
        """Generate response from OpenAI, supporting patient detail function calls (multi-turn)"""
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
            functions = [GET_PATIENT_DETAILS_BY_NAME_FUNCTION]
            while True:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    functions=functions,
                    function_call="auto",
                    temperature=0.7,
                    max_tokens=1000
                )
                choice = response.choices[0].message
                if choice.function_call:
                    fn_name = choice.function_call.name
                    args = choice.function_call.arguments
                    import json
                    fn_args = json.loads(args) if isinstance(args, str) else args
                    if fn_name == "get_patient_details":
                        fn_result = await get_patient_details(**fn_args)
                    elif fn_name == "get_patient_details_by_name":
                        fn_result = await get_patient_details_by_name(**fn_args)
                    else:
                        raise HTTPException(status_code=400, detail=f"Unknown function: {fn_name}")
                    openai_messages.append({
                        "role": "function",
                        "name": fn_name,
                        "content": str(fn_result)
                    })
                    continue  # Check if model wants to call another function
                elif choice.content:
                    return choice.content
                else:
                    raise HTTPException(status_code=500, detail="No valid response from OpenAI.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
