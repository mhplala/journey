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
import os
import aiohttp

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

# In-memory storage for conversations and topics
conversations: Dict[str, dict] = {}
topics: Dict[str, dict] = {}

class Message(BaseModel):
    role: str
    content: str
    agent: str
    timestamp: str

class CreateConversationRequest(BaseModel):
    agent_count: int = 2  # Default to 2 agents
    topic: Optional[str] = None
    round_count: Optional[int] = 2  # Default to 2 rounds

class ChatRequest(BaseModel):
    conversation_id: str
    agent: str
    message: str

PERSONALITIES = [
    "analytical and logical",
    "creative and imaginative",
    "practical and grounded",
    "optimistic and enthusiastic",
    "skeptical and questioning"
]

async def call_deepseek_api(prompt: str) -> str:
    """Call DeepSeek API to generate response."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "sk-ee8827e619f2436183348920a525a7b7")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            async with session.post(f"{api_base}/v1/chat/completions", headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"Error generating response: {error_text}"
        except Exception as e:
            return f"Error calling DeepSeek API: {str(e)}"

def generate_agent_names(count: int) -> List[str]:
    name_list = [
        "Alice", "Bernard", "Chen", "Diana", "Elena", 
        "Farhan", "Grace", "Hassan", "Isabella", "James"
    ]
    return random.sample(name_list, min(count, len(name_list)))

async def generate_agent_response(agent: str, personality: str, topic: str, history: List[Message]) -> str:
    """Generate a response for an agent based on their personality and conversation history."""
    history_text = "\n".join([f"{msg.agent}: {msg.content}" for msg in history])
    prompt = f"""You are {agent}, an AI with a {personality} personality.
Topic: {topic}

Previous messages:
{history_text}

Provide your thoughts on the topic, staying true to your {personality} personality."""
    
    return await call_deepseek_api(prompt)

async def generate_summary(topic: str, messages: List[Message]) -> str:
    """Generate a summary of the conversation by Steve."""
    history_text = "\n".join([f"{msg.agent}: {msg.content}" for msg in messages])
    prompt = f"""As Steve, provide a concise summary of this discussion about '{topic}'.
    
Conversation:
{history_text}

Summarize the key points and insights shared by all participants."""
    
    return await call_deepseek_api(prompt)

async def run_autonomous_discussion(conversation: dict):
    """Run an autonomous discussion between agents"""
    try:
        conversation["is_auto_playing"] = True
        while (conversation["current_round"] <= conversation["max_rounds"] and 
               len(conversation["messages"]) < len(conversation["agents"]) * conversation["max_rounds"] and
               not conversation.get("stopped", False)):
            
            current_agent_idx = len(conversation["messages"]) % len(conversation["agents"])
            current_agent = conversation["agents"][current_agent_idx]
            
            # Generate response
            response = await generate_agent_response(
                current_agent,
                conversation["agent_personalities"][current_agent],
                conversation["topic"],
                conversation["messages"]
            )
            
            # Add message
            new_message = Message(
                role="assistant",
                content=response,
                agent=current_agent,
                timestamp=datetime.now().isoformat()
            )
            conversation["messages"].append(new_message)
            
            # Update round if all agents have spoken
            if len(conversation["messages"]) % len(conversation["agents"]) == 0:
                conversation["current_round"] += 1
                
                # Generate summary if conversation is complete
                if conversation["current_round"] > conversation["max_rounds"]:
                    conversation["summary"] = await generate_summary(
                        conversation["topic"],
                        conversation["messages"]
                    )
            
            # Small delay between messages
            await asyncio.sleep(2)
    finally:
        conversation["is_auto_playing"] = False

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/conversations")
async def create_conversation(request: CreateConversationRequest, background_tasks: BackgroundTasks):
    if request.agent_count < 2 or request.agent_count > 10:
        raise HTTPException(
            status_code=400,
            detail="Agent count must be between 2 and 10"
        )
    
    conversation_id = str(uuid.uuid4())
    agents = generate_agent_names(request.agent_count)
    agent_personalities = {
        agent: random.choice(PERSONALITIES)
        for agent in agents
    }
    
    conversation = {
        "id": conversation_id,
        "topic": request.topic,
        "messages": [],
        "current_round": 1,
        "max_rounds": request.round_count,
        "agents": agents,
        "agent_personalities": agent_personalities,
        "summary": None,
        "is_auto_playing": False,
        "stopped": False
    }
    
    conversations[conversation_id] = conversation
    topics[conversation_id] = {
        "id": conversation_id,
        "text": request.topic,
        "timestamp": datetime.now().isoformat()
    }
    
    # Start autonomous discussion in background
    background_tasks.add_task(run_autonomous_discussion, conversation)
    
    return conversation

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.get("/api/topics")
async def get_topics():
    """Get all topics in chronological order"""
    return {"topics": sorted(
        list(topics.values()),
        key=lambda x: x["timestamp"],
        reverse=True
    )}

@app.post("/api/conversations/{conversation_id}/stop")
async def stop_conversation(conversation_id: str):
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation["stopped"] = True
    return {"status": "success", "message": "Conversation stopped"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
