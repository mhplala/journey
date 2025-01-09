import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { stopConversation, getTopics, createConversation, BASE_URL } from './lib/api'
import { Topic, Message } from './lib/types'
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, Plus, Loader2 } from 'lucide-react'

// Styles for simplified UI
const styles = {
  container: "container mx-auto p-4 flex h-screen",
  leftPanel: "w-64 pr-4 flex flex-col",
  mainArea: "flex-1 flex flex-col",
  card: "flex-1 mb-4",
  messageContainer: "p-4 rounded-lg bg-secondary",
  summaryContainer: "p-4 rounded-lg bg-primary/10",
  loadingSpinner: "mr-2 h-4 w-4 animate-spin"
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
        if (data.summary) {
          const conv = conversations.find(c => c.id === currentConversation)
          if (conv) {
            conv.summary = data.summary
            setConversations([...conversations])
          }
        }
        // Update conversation status
        if (data.is_auto_playing !== undefined) {
          const conv = conversations.find(c => c.id === currentConversation)
          if (conv) {
            conv.is_auto_playing = data.is_auto_playing
            setConversations([...conversations])
          }
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
      // Use fixed values for agent count and rounds
      const result = await createConversation(3, newTopic, 10)
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
    } catch (error) {
      console.error('Failed to create conversation:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch topics periodically
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const fetchedTopics = await getTopics();
        setTopics(fetchedTopics);
      } catch (error) {
        console.error('Failed to fetch topics:', error);
      }
    };

    fetchTopics();
    const interval = setInterval(fetchTopics, 5000);
    return () => clearInterval(interval);
  }, []);

  const getCurrentConversation = () => {
    return conversations.find(conv => conv.id === currentConversation)
  }

  return (
    <div className={styles.container}>
      {/* Left Panel - Topic Input and Active Conversations */}
      <div className={styles.leftPanel}>
          <Card className="p-4">
            <CardHeader>
              <CardTitle>Start an AI Discussion</CardTitle>
              <p className="text-sm text-muted-foreground">
                Enter a topic and watch AI agents discuss it automatically
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
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
                <Button 
                  className="w-full"
                  onClick={createNewConversation}
                  disabled={!newTopic || isLoading || getCurrentConversation()?.is_auto_playing}
                >
                  {isLoading ? (
                    <Loader2 className={styles.loadingSpinner} />
                  ) : (
                    <Plus className="mr-2 h-4 w-4" />
                  )}
                  {isLoading ? 'Starting Discussion...' : 'Start Discussion'}
                </Button>
                {getCurrentConversation()?.is_auto_playing && (
                  <div className="text-sm text-center text-muted-foreground animate-pulse">
                    AI agents are discussing your topic...
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
            
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
                      onClick={() => stopConversation(getCurrentConversation()?.id || '')}
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
                {topics.map(topic => (
                  <Card key={topic.id} className="cursor-pointer hover:bg-secondary/10">
                    <CardHeader className="p-4">
                      <CardTitle className="text-sm">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <MessageSquare className="mr-2 h-4 w-4" />
                            {topic.text}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(topic.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </CardTitle>
                    </CardHeader>
                  </Card>
                ))}
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
            <CardContent className="h-full overflow-y-auto space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={styles.messageContainer}>
                  <div className="flex items-center mb-2">
                    <strong className="mr-2">{msg.agent}</strong>
                    <span className="text-sm text-muted-foreground">
                      ({getCurrentConversation()?.agent_personalities[msg.agent]})
                    </span>
                  </div>
                  <p className="text-sm">{msg.content}</p>
                </div>
              ))}
              {getCurrentConversation()?.summary && (
                <div className={styles.summaryContainer}>
                  <h3 className="font-semibold mb-2">Discussion Summary</h3>
                  <p className="text-sm">{getCurrentConversation()?.summary}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
  )
}

export default App
