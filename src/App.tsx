import { useState, useEffect } from 'react'
import { formatMessageText } from '@/lib/text-utils'
import { Button } from "@/components/ui/button"
import TypewriterText from './components/TypewriterText'
import { stopConversation, getTopics, createConversation, loadHistoricalConversation, BASE_URL } from './lib/api'
import { Topic, Message } from './lib/types'
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, Plus, Loader2 } from 'lucide-react'

// Styles for simplified UI
const styles = {
  container: "container mx-auto p-4 flex h-screen",
  leftPanel: "w-64 pr-4 flex flex-col overflow-y-auto",
  mainArea: "flex-1 flex flex-col relative",
  card: "flex-1 mb-4 overflow-hidden flex flex-col",
  messageContainer: "p-4 rounded-lg bg-secondary",
  summaryContainer: "p-4 rounded-lg bg-primary/10",
  loadingSpinner: "mr-2 h-4 w-4 animate-spin",
  inputContainer: "absolute bottom-0 left-0 right-0 p-4 bg-background border-t"
};

interface Conversation {
  id: string;
  topic?: string;
  agents: string[];
  agent_personalities: { [key: string]: string };
  messages: Message[];
  currentRound: number;
  maxRounds: number;
  summary?: string;
  is_auto_playing?: boolean;
  stopped?: boolean;
}

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<string | null>(null)
  const [newTopic, setNewTopic] = useState<string>('')
  const [topics, setTopics] = useState<Topic[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [agentCount, setAgentCount] = useState<number>(3)
  const [roundCount, setRoundCount] = useState<number>(10)

  // Poll for conversation updates
  useEffect(() => {
    if (!currentConversation) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/conversations/${currentConversation}`)
        const data = await response.json()
        if (data.messages) {
          setMessages(data.messages)
        }
        if (data.summary || data.is_auto_playing !== undefined) {
          setConversations(prevConversations => {
            return prevConversations.map(conv => {
              if (conv.id === currentConversation) {
                return {
                  ...conv,
                  summary: data.summary || conv.summary,
                  is_auto_playing: data.is_auto_playing ?? conv.is_auto_playing
                }
              }
              return conv
            })
          })
        }
      } catch (error) {
        console.error('Failed to poll conversation:', error)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [currentConversation])

  const createNewConversation = async () => {
    if (!newTopic || isLoading) return
    setIsLoading(true)
    try {
      const result = await createConversation(agentCount, newTopic, roundCount)
      const newConversation: Conversation = {
        id: result.conversation_id,
        topic: result.topic,
        agents: result.agents,
        agent_personalities: result.agent_personalities,
        messages: [],
        currentRound: result.current_round,
        maxRounds: result.max_rounds,
        summary: undefined,
        is_auto_playing: true
      }
      setConversations([...conversations, newConversation])
      setCurrentConversation(newConversation.id)
      setMessages([])
      setNewTopic('') // Clear input after creating conversation
      await fetchTopics(); // Refresh topics after creating conversation
    } catch (error) {
      console.error('Failed to create conversation:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch topics function
  const fetchTopics = async () => {
    try {
      const fetchedTopics = await getTopics();
      setTopics(fetchedTopics);
    } catch (error) {
      console.error('Failed to fetch topics:', error);
    }
  };

  // Fetch topics periodically
  useEffect(() => {
    fetchTopics();
    const interval = setInterval(fetchTopics, 5000);
    return () => clearInterval(interval);
  }, []);

  const getCurrentConversation = () => {
    return conversations.find(conv => conv.id === currentConversation)
  }

  return (
    <div className={styles.container}>
      {/* Left Panel - Previous Conversations */}
      <div className={styles.leftPanel}>
            
          {/* Active Conversation */}
          {getCurrentConversation() && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    {getCurrentConversation()?.topic || 'No Topic'}
                  </div>
                  {getCurrentConversation()?.is_auto_playing && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={async () => {
                        try {
                          await stopConversation(getCurrentConversation()?.id || '');
                          await fetchTopics(); // Refresh topics after stopping conversation
                        } catch (error) {
                          console.error('Failed to stop conversation:', error);
                        }
                      }}
                    >
                      Stop Discussion
                    </Button>
                  )}
                </CardTitle>
                {getCurrentConversation()?.is_auto_playing && (
                  <div className="text-sm text-center text-muted-foreground animate-pulse mt-2">
                    Agents are discussing...
                  </div>
                )}
              </CardHeader>
            </Card>
          )}
          
          {/* Topics History */}
          {topics.length > 0 && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>Previous Discussions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {topics.map(topic => {
                  const isLoading = currentConversation === topic.conversation_id;
                  return (
                    <Card 
                      key={topic.id} 
                      className={`cursor-pointer hover:bg-secondary/10 ${isLoading ? 'opacity-50' : ''}`}
                      onClick={async () => {
                        try {
                          setIsLoading(true);
                          const historicalConversation = await loadHistoricalConversation(topic.conversation_id);
                          setCurrentConversation(topic.conversation_id);
                          setMessages(historicalConversation.messages || []);
                          const conv = {
                            id: historicalConversation.id,
                            topic: topic.text,
                            agents: historicalConversation.agents,
                            agent_personalities: historicalConversation.agent_personalities,
                            messages: historicalConversation.messages,
                            currentRound: historicalConversation.current_round,
                            maxRounds: historicalConversation.max_rounds,
                            summary: historicalConversation.summary,
                            is_auto_playing: false,
                            stopped: true
                          };
                          setConversations(prevConvs => {
                            const existing = prevConvs.find(c => c.id === conv.id);
                            if (existing) {
                              return prevConvs.map(c => c.id === conv.id ? conv : c);
                            }
                            return [...prevConvs, conv];
                          });
                        } catch (error) {
                          console.error('Failed to load historical conversation:', error);
                        } finally {
                          setIsLoading(false);
                        }
                      }}
                    >
                      <CardHeader className="p-4">
                        <CardTitle className="text-sm">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <MessageSquare className="mr-2 h-4 w-4" />
                              {topic.text}
                              {isLoading && <Loader2 className="ml-2 h-4 w-4 animate-spin" />}
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {new Date(topic.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  );
                })}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main Chat Area */}
        <div className={styles.mainArea}>
          <Card className={styles.card}>
            <CardHeader>
              <CardTitle>
                {getCurrentConversation() 
                  ? `Discussion: ${getCurrentConversation()?.topic}` 
                  : 'Enter a topic to start a discussion'}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto space-y-4 pb-24">
              {messages.map((msg, i) => (
                <div 
                  key={i} 
                  className={`${styles.messageContainer} transition-all duration-300 ease-in-out transform hover:scale-[1.02] hover:shadow-lg`}
                >
                  <div className="flex items-center mb-2">
                    <strong className="mr-2">{msg.agent}</strong>
                    <span className="text-sm text-muted-foreground">
                      ({formatMessageText(getCurrentConversation()?.agent_personalities[msg.agent] || '')})
                    </span>
                  </div>
                  <div className="text-sm whitespace-pre-wrap">
                    <TypewriterText text={formatMessageText(msg.content)} />
                  </div>
                </div>
              ))}
              {getCurrentConversation()?.summary && (
                <div className={`${styles.summaryContainer} transition-all duration-300 ease-in-out transform hover:scale-[1.02] hover:shadow-lg`}>
                  <h3 className="font-semibold mb-2 flex items-center">
                    <span className="mr-2">📝</span>
                    Discussion Summary
                  </h3>
                  <div className="text-sm whitespace-pre-wrap">
                    <TypewriterText text={formatMessageText(getCurrentConversation()?.summary || '')} />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Input Container */}
        <div className={styles.inputContainer}>
          <div className="space-y-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <Input
                  type="text"
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  placeholder="Enter a topic for discussion"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newTopic && !isLoading) {
                      createNewConversation()
                    }
                  }}
                  disabled={isLoading || getCurrentConversation()?.is_auto_playing}
                />
              </div>
              <div className="flex space-x-2">
                <Input
                  type="number"
                  min={2}
                  max={10}
                  value={agentCount}
                  onChange={(e) => setAgentCount(Math.min(10, Math.max(2, parseInt(e.target.value) || 2)))}
                  disabled={isLoading || getCurrentConversation()?.is_auto_playing}
                  className="w-20"
                  placeholder="Agents"
                />
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={roundCount}
                  onChange={(e) => setRoundCount(Math.min(20, Math.max(1, parseInt(e.target.value) || 1)))}
                  disabled={isLoading || getCurrentConversation()?.is_auto_playing}
                  className="w-20"
                  placeholder="Rounds"
                />
                <Button 
                  onClick={createNewConversation}
                  disabled={!newTopic || isLoading || getCurrentConversation()?.is_auto_playing}
                >
                  {isLoading ? (
                    <Loader2 className={styles.loadingSpinner} />
                  ) : (
                    <Plus className="mr-2 h-4 w-4" />
                  )}
                  {isLoading ? '...' : 'Start'}
                </Button>
              </div>
            </div>
            {getCurrentConversation()?.is_auto_playing && (
              <div className="text-sm text-center text-muted-foreground animate-pulse">
                AI agents are discussing your topic...
              </div>
            )}
          </div>
        </div>
      </div>
  )
}

export default App
