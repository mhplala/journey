from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from .services.deepseek_service import DeepSeekService
from .models.conversation import Conversation, Message
import uuid

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize DeepSeek service
deepseek_service = DeepSeekService()

# In-memory storage for conversations
conversations: Dict[str, Conversation] = {}

class CreateConversationRequest(BaseModel):
    agent_count: int

class ChatRequest(BaseModel):
    conversation_id: str
    agent: str
    message: str

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/conversations")
async def create_conversation(request: CreateConversationRequest):
    if request.agent_count < 2 or request.agent_count > 10:
        raise HTTPException(
            status_code=400,
            detail="Agent count must be between 2 and 10"
        )
    
    conversation_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conversation_id,
        agents=[f"Agent {i+1}" for i in range(request.agent_count)]
    )
    conversations[conversation_id] = conversation
    
    return {
        "conversation_id": conversation_id,
        "agents": conversation.agents,
        "current_round": 0,
        "max_rounds": conversation.max_rounds
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation.id,
        "agents": conversation.agents,
        "messages": conversation.messages,
        "current_round": conversation.current_round,
        "max_rounds": conversation.max_rounds,
        "next_agent": conversation.get_next_agent()
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    conversation = conversations.get(request.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    next_agent = conversation.get_next_agent()
    if not next_agent:
        raise HTTPException(status_code=400, detail="Conversation has ended")
    
    if next_agent != request.agent:
        raise HTTPException(
            status_code=400,
            detail=f"It's {next_agent}'s turn to speak"
        )
    
    try:
        # Get context and generate response
        context = conversation.get_context_for_agent(request.agent)
        context.append({"role": "user", "content": request.message})
        
        response = await deepseek_service.generate_response(context)
        next_agent = conversation.add_message(response, request.agent)
        
        # Generate summary if this was the last message (next_agent is None)
        if next_agent is None and not conversation.summary:
            print(f"Generating summary for conversation {conversation.id}")  # Debug log
            summary_context = [
                {
                    "role": "system",
                    "content": (
                        "You are a summary agent tasked with providing a comprehensive summary "
                        "of a completed conversation. Focus on the key points discussed, "
                        "agreements reached, and main conclusions. Structure your summary "
                        "clearly with main topics and their outcomes. Be thorough but concise."
                    )
                }
            ]
            
            # Add all messages to context as a single message
            messages_text = "\n".join([f"{msg.agent}: {msg.content}" for msg in conversation.messages])
            summary_context.append({
                "role": "user",
                "content": (
                    "Please provide a structured summary of this conversation. Include:\n"
                    "1. Key topics discussed\n"
                    "2. Main arguments and viewpoints\n"
                    "3. Areas of agreement\n"
                    "4. Final conclusions\n\n"
                    f"Conversation:\n{messages_text}"
                )
            })
            
            print("Requesting summary from DeepSeek API...")  # Debug log
            conversation.summary = await deepseek_service.generate_response(summary_context)
            print("Summary generated successfully")  # Debug log
        
        return {
            "response": response,
            "current_round": conversation.current_round,
            "next_agent": next_agent,
            "messages": conversation.messages,
            "summary": conversation.summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
