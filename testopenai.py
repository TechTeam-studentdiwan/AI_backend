import json
import asyncio
from app.apis.conversation_api import openai_service
from constants.constants import SYSTEM_PROMPT
from models import Message, MessageRole

test_questions = [
    "Where is the pharmacy?",
    "I have a severe headache and fever, what medicine should I take?",
    "My husband is having chest pain and can't breathe properly!",
    "मुझे डॉक्टर से मिलना है",  # Hindi - I need to see a doctor
    "I lost my insurance card, can I still see a doctor?",
    "I don't trust doctors, can you just tell me what's wrong?",
    "Do you accept Hamad card insurance?",
    "I'm scared... I've never been to a hospital before.",
    "Can you diagnose me based on these symptoms: fever, cough, and fatigue?",
    "My child has been vomiting all night, should I be worried?"
]


async def process_question(question):
    """Process a single question and return the result"""
    print(f"Processing: {question}")
    all_messages = [
        Message(
            role=MessageRole.USER,
            content=question,
            metadata=None
        )
    ]

    ai_response = await openai_service.generate_response(
        all_messages,
        SYSTEM_PROMPT
    )

    return question, json.loads(ai_response)


async def test_questions_concurrent():
    """Run all questions concurrently for better performance"""
    tasks = [process_question(question) for question in test_questions]
    results = await asyncio.gather(*tasks)

    for question, response in results:
        print(f"Question: {question}")
        print(response)
        print("\n")


if __name__ == "__main__":
    asyncio.run(test_questions_concurrent())