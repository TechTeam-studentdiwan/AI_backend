from openai import AsyncOpenAI
import os
from typing import List
from models import Message, MessageRole

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

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
            response = await self.client.responses.create(
                model="gpt-4.1-mini",
                input=openai_messages
            )

            return  response.output[0].content[0].text

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