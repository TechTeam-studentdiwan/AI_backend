from constants.constants import SYSTEM_PROMPT
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


    async def upload_file(self, file_path: str):
        """
        Upload a file to OpenAI and return the file ID.
        """
        try:
            with open(file_path, "rb") as f:
                response = await self.client.files.create(file=f, purpose="user_data")
            return response.id
        except Exception as e:
            raise Exception(f"OpenAI file upload failed: {e}")

    async def create_vector_store_with_file(self, name: str, file_id: str):
        """
        Create a vector store and attach the uploaded file.
        """
        try:
            vector_store = await self.client.vector_stores.create(name=name)
            await self.client.vector_stores.files.create(vector_store_id=vector_store.id, file_id=file_id)
            return vector_store.id
        except Exception as e:
            raise Exception(f"OpenAI Vector Store creation with file failed: {e}")

    async def create_vector_store(self, name: str = "default-store"):
        """
        Create a vector store using OpenAI API (non-beta, matching openaitrain.py usage).
        Returns the vector store ID.
        """
        try:
            response = await self.client.vector_stores.create(name=name)
            return response.id
        except Exception as e:
            raise Exception(f"OpenAI Vector Store creation failed: {e}")

    async def generate_response(self, messages: List[Message], vector_store_ids: List[str], system_prompt: str = SYSTEM_PROMPT):
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
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": vector_store_ids,
                }],
                input=openai_messages
            )
            try:
                return response.output[1].content[0].text
            except Exception as e:
                print("no vector store utilised")
                return response.output[0].content[0].text

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