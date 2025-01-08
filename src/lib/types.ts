export interface Message {
  role: string;
  content: string;
  agent: string;
  timestamp: string;
}

export interface ConversationResponse {
  conversation_id: string;
  topic?: string;
  agents: string[];
  agent_personalities: { [key: string]: string };
  current_round: number;
  max_rounds: number;
  is_auto_playing?: boolean;
  stopped?: boolean;
}

export interface ChatResponse {
  response: string;
  current_round: number;
  next_agent: string | null;
  messages: Message[];
  summary?: string;
}

export interface Topic {
  id: string;
  text: string;
  conversation_id: string;
  timestamp: string;
  summary?: string;
  agents: string[];
  agent_personalities: { [key: string]: string };
  messages: Message[];
}
