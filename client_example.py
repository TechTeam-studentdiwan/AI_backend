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