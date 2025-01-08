import axios from 'axios';
import { ConversationResponse, ChatResponse, Topic } from './types';

const API_BASE_URL = 'http://45.76.190.47/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const createConversation = async (
  agentCount: number,
  topic?: string,
  roundCount: number = 10
): Promise<ConversationResponse> => {
  const response = await api.post<ConversationResponse>('/conversations', {
    agent_count: agentCount,
    topic,
    round_count: roundCount
  });
  return response.data;
};

export const sendMessage = async (conversationId: string, agent: string, message: string): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('/chat', {
    conversation_id: conversationId,
    agent,
    message,
  });
  return response.data;
};

export const stopConversation = async (conversationId: string): Promise<void> => {
  await api.post(`/conversations/${conversationId}/stop`);
};

export const getTopics = async (): Promise<Topic[]> => {
  const response = await api.get<{ topics: Topic[] }>('/topics');
  return response.data.topics;
};

export const getTopic = async (topicId: string) => {
  const response = await api.get(`/topics/${topicId}`);
  return response.data;
};

export default api;
