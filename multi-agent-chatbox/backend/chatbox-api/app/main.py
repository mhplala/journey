from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import asyncio
import json
import logging
import random

from .services.deepseek_service import DeepSeekService
from .models.conversation import Conversation, Message, Topic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize DeepSeek service
deepseek_service = DeepSeekService()

# In-memory storage for conversations and topics
conversations: Dict[str, Conversation] = {}
topics: Dict[str, Topic] = {}

class CreateConversationRequest(BaseModel):
    agent_count: int
    topic: Optional[str] = None
    round_count: Optional[int] = 10

class ChatRequest(BaseModel):
    conversation_id: str
    agent: str
    message: str

# Health check endpoint
@app.get("/api/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/api/topics", tags=["chat"], response_model=dict)
async def get_topics():
    """Get all topics in chronological order"""
    return {"topics": sorted(
        [topic.dict() for topic in topics.values()],
        key=lambda x: x["timestamp"],
        reverse=True
    )}

async def run_autonomous_discussion(conversation: Conversation):
    """Run an autonomous discussion between agents"""
    try:
        conversation.is_auto_playing = True
        while not conversation.is_completed and not conversation.stopped:
            current_agent = conversation.get_next_agent()
            if not current_agent:
                break
                
            # Get context and generate response
            context = conversation.get_context_for_agent(current_agent)
            if not conversation.messages:  # First message
                context.append({"role": "user", "content": f"Start a discussion about {conversation.topic}. Remember to stay in character and express your views based on your personality."})
            
            response = await deepseek_service.generate_response(context)
            conversation.add_message(response, current_agent)
            
            # Small delay between messages
            await asyncio.sleep(2)
            
        # Generate summary if conversation completed normally
        if not conversation.stopped and not conversation.summary:
            summary_context = [
                {
                    "role": "system",
                    "content": "You are a summary agent tasked with providing a comprehensive summary of a completed conversation. Focus on the key points discussed, agreements reached, and main conclusions."
                }
            ]
            messages_text = "\n".join([f"{msg.agent}: {msg.content}" for msg in conversation.messages])
            summary_context.append({
                "role": "user",
                "content": f"Please summarize this conversation about {conversation.topic}:\n{messages_text}"
            })
            conversation.summary = await deepseek_service.generate_response(summary_context)
    finally:
        conversation.is_auto_playing = False

@app.post("/api/conversations", tags=["chat"])
async def create_conversation(request: CreateConversationRequest, background_tasks: BackgroundTasks):
    if request.agent_count < 2 or request.agent_count > 10:
        raise HTTPException(
            status_code=400,
            detail="Agent count must be between 2 and 10"
        )
    
    conversation_id = str(uuid.uuid4())
    # List of diverse names for agents
    name_list = [
        "Alice", "Bernard", "Chen", "Diana", "Elena", 
        "Farhan", "Grace", "Hassan", "Isabella", "James",
        "Karim", "Luna", "Miguel", "Nina", "Omar",
        "Priya", "Quinn", "Ravi", "Sofia", "Tao",
        "Uma", "Victor", "Wei", "Xena", "Yuki",
        "Zara", "Adam", "Bianca", "Carlos", "Devi"
    ]
    
    # Handle case where we need more agents than available names
    if request.agent_count > len(name_list):
        # Use available names and add numbered agents for the rest
        available_names = name_list.copy()
        agents = random.sample(available_names, len(available_names))
        remaining_count = request.agent_count - len(available_names)
        agents.extend([f"Agent {i+1}" for i in range(remaining_count)])
    else:
        # Randomly select names from the list
        agents = random.sample(name_list, request.agent_count)
    
    # Keep existing personality assignment logic
    personalities = random.sample(Conversation.PERSONALITIES, len(agents))
    agent_personalities = {agent: personality for agent, personality in zip(agents, personalities)}
    
    conversation = Conversation(
        id=conversation_id,
        topic=request.topic,
        agents=agents,
        agent_personalities=agent_personalities,
        max_rounds=request.round_count or 10  # Default to 10 if None
    )
    conversations[conversation_id] = conversation
    
    # Start autonomous discussion in background
    background_tasks.add_task(run_autonomous_discussion, conversation)
    
    return {
        "conversation_id": conversation_id,
        "topic": conversation.topic,
        "agents": conversation.agents,
        "agent_personalities": conversation.agent_personalities,
        "current_round": 0,
        "max_rounds": conversation.max_rounds
    }

# Topics endpoint moved to top level with other routes

@app.get("/api/topics/{topic_id}", tags=["chat"])
async def get_topic(topic_id: str):
    topic = topics.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@app.post("/api/conversations/{conversation_id}/stop", tags=["chat"])
async def stop_conversation(conversation_id: str):
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.stopped = True
    
    # If conversation has a topic, store it in topics history
    if conversation.topic:
        topic_id = str(uuid.uuid4())
        topics[topic_id] = Topic(
            id=topic_id,
            text=conversation.topic,
            conversation_id=conversation.id,
            timestamp=datetime.now(),
            summary=conversation.summary,
            agents=conversation.agents,
            agent_personalities=conversation.agent_personalities,
            messages=conversation.messages
        )
    
    return {"status": "success", "message": "Conversation stopped"}

@app.get("/api/conversations", tags=["chat"], response_model=list)
async def list_conversations():
    """List all active conversations"""
    return [
        {
            "conversation_id": conv.id,
            "topic": conv.topic,
            "agents": conv.agents,
            "current_round": conv.current_round,
            "max_rounds": conv.max_rounds,
            "is_auto_playing": conv.is_auto_playing,
            "stopped": conv.stopped
        }
        for conv in conversations.values()
    ]

@app.get("/api/conversations/{conversation_id}", tags=["chat"])
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
        "next_agent": conversation.get_next_agent(),
        "is_auto_playing": conversation.is_auto_playing,
        "stopped": conversation.stopped
    }

@app.post("/api/chat", tags=["chat"])
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
