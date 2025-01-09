import { Topic } from './types';

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createConversation(agentCount: number, topic: string, roundCount: number) {
  const response = await fetch(`${BASE_URL}/api/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ agent_count: agentCount, topic, round_count: roundCount }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create conversation');
  }
  
  return response.json();
}

export async function stopConversation(conversationId: string) {
  const response = await fetch(`${BASE_URL}/api/conversations/${conversationId}/stop`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to stop conversation');
  }
  
  return response.json();
}

export async function getTopics(): Promise<Topic[]> {
  const response = await fetch(`${BASE_URL}/api/topics`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch topics');
  }
  
  const data = await response.json();
  return data.topics;
}

export async function loadHistoricalConversation(conversationId: string) {
  const response = await fetch(`${BASE_URL}/api/conversations/${conversationId}`);
  
  if (!response.ok) {
    throw new Error('Failed to load historical conversation');
  }
  
  return response.json();
}
