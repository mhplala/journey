from pydantic import BaseModel
from typing import List, Dict, Optional, ClassVar
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str
    agent: str
    timestamp: datetime = datetime.now()

class Topic(BaseModel):
    id: str
    text: str
    conversation_id: str
    timestamp: datetime
    summary: Optional[str]
    agents: List[str]
    agent_personalities: Dict[str, str]
    messages: List[Message]

class Conversation(BaseModel):
    id: str
    topic: Optional[str] = None
    agents: List[str]
    agent_personalities: Dict[str, str] = {}
    messages: List[Message] = []
    current_round: int = 0
    max_rounds: int = 10
    current_agent_index: int = 0
    summary: Optional[str] = None
    stopped: bool = False
    is_auto_playing: bool = False

    PERSONALITIES: ClassVar[List[str]] = [
        "The Optimist who sees opportunities in challenges",
        "The Critic who questions assumptions",
        "The Pragmatist who focuses on practical solutions",
        "The Innovator who thinks outside the box",
        "The Analyst who examines data and facts",
        "The Mediator who finds common ground",
        "The Devil's Advocate who challenges ideas",
        "The Visionary who considers long-term implications",
        "The Expert who provides technical insights",
        "The Synthesizer who connects different viewpoints"
    ]
    
    @property
    def is_completed(self) -> bool:
        """Check if the conversation has completed all rounds"""
        return self.current_round >= self.max_rounds
        
    @property
    def is_last_message(self) -> bool:
        """Check if this is the last message of the last round"""
        return (self.current_round == self.max_rounds - 1 and 
                self.current_agent_index == len(self.agents) - 1)

    def get_next_agent(self) -> Optional[str]:
        """Get the next agent without advancing the turn"""
        if self.current_round >= self.max_rounds:
            return None
        return self.agents[self.current_agent_index]

    def advance_turn(self) -> Optional[str]:
        """Advance to the next turn and return the next agent"""
        # First increment the agent index
        self.current_agent_index = (self.current_agent_index + 1) % len(self.agents)
        
        # If we've completed a round
        if self.current_agent_index == 0:
            self.current_round += 1
            
        # Check if we've exceeded max rounds
        if self.current_round >= self.max_rounds:
            return None
            
        return self.get_next_agent()

    def add_message(self, content: str, agent: str) -> Optional[str]:
        """Add a message and advance the turn"""
        # Add the message
        self.messages.append(Message(
            role="assistant",
            content=content,
            agent=agent
        ))
        
        # Get next agent (will be None if conversation is complete)
        next_agent = self.advance_turn()
        
        # If this was the last message, prepare for summary
        if next_agent is None:
            print(f"Conversation {self.id} completed {self.max_rounds} rounds. Ready for summary.")
            
        return next_agent

    def get_context_for_agent(self, agent: str) -> List[Dict[str, str]]:
        """Get conversation context formatted for DeepSeek API"""
        # System message to define the agent's role and personality
        personality = self.agent_personalities.get(agent, "a neutral participant")
        system_prompt = f"""You are {agent}, {personality} in a multi-agent conversation about '{self.topic}'.
Your responses should reflect your assigned personality trait while discussing the topic.
Respond naturally and concisely to the latest message. Do not repeat previous messages."""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Add only the last few messages for context
        context_messages = self.messages[-4:] if len(self.messages) > 4 else self.messages
        for msg in context_messages:
            messages.append({
                "role": "assistant" if msg.agent == agent else "user",
                "content": msg.content
            })
            
        return messages
