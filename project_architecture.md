# MongoDB Conversation Management System with FastAPI - Architecture

```mermaid
classDiagram
    class Models {
        +MessageRole
        +Message
        +Conversation
        +StartConversationRequest
        +StartConversationResponse
        +AddMessageRequest
        +ConversationHistoryResponse
    }

    class Database {
        +MongoDB
        +connect_to_mongo()
        +close_mongo_connection()
        +create_conversation()
        +get_conversation()
        +update_conversation()
        +add_message_to_conversation()
        +get_user_conversations()
    }

    class OpenAIService {
        +generate_response()
        +generate_conversation_title()
    }

    class FastAPIApp {
        +start_conversation()
        +get_conversation_history()
        +add_message()
        +get_user_conversations_list()
        +delete_conversation()
    }

    class Environment {
        +MONGODB_URL
        +DB_NAME
        +OPENAI_API_KEY
        +OPENAI_MODEL
    }

    Models --> Database : Uses
    Models --> FastAPIApp : Uses
    Database --> FastAPIApp : Uses
    OpenAIService --> FastAPIApp : Uses
    Environment --> FastAPIApp : Configures
    Environment --> OpenAIService : Configures

    class Dependencies {
        +fastapi
        +uvicorn
        +motor
        +pymongo
        +pydantic
        +openai
        +python-dotenv
    }

    FastAPIApp --> Dependencies : Requires
    OpenAIService --> Dependencies : Requires
    Database --> Dependencies : Requires