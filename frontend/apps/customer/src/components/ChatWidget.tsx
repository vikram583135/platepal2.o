import { useState, useEffect, useRef } from 'react'
import { X, Send, Image as ImageIcon } from 'lucide-react'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { formatDate } from '@/packages/utils/format'
import { useAuthStore } from '../stores/authStore'
import { createChatWebSocket } from '@/packages/api/chat'
import apiClient from '@/packages/api/client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

interface ChatWidgetProps {
  roomId: number
  orderId?: number
  onClose?: () => void
  isMinimized?: boolean
  onMinimize?: () => void
}

interface ChatMessage {
  id: number
  sender: number
  sender_name: string
  sender_email: string
  sender_photo?: string
  message_type: string
  content: string
  image_url?: string
  file_url?: string
  is_read: boolean
  created_at: string
}

export default function ChatWidget({ roomId, orderId, onClose, isMinimized, onMinimize }: ChatWidgetProps) {
  const { user, token } = useAuthStore()
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [typingUser, setTypingUser] = useState<string | null>(null)
  const [ws, setWs] = useState<ReturnType<typeof createChatWebSocket> | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const queryClient = useQueryClient()

  // Fetch messages
  const { data: fetchedMessages, refetch } = useQuery({
    queryKey: ['chat-messages', roomId],
    queryFn: async () => {
      const response = await apiClient.get(`/chat/messages/?room_id=${roomId}`)
      return response.data.results || response.data || []
    },
  })

  useEffect(() => {
    if (fetchedMessages) {
      setMessages(fetchedMessages)
    }
  }, [fetchedMessages])

  // WebSocket connection
  useEffect(() => {
    if (!token || !roomId) return

    const chatWs = createChatWebSocket(roomId, token)
    
    chatWs.on('chat_message', (event: any) => {
      if (event.data) {
        setMessages((prev) => [...prev, event.data])
        scrollToBottom()
      }
    })

    chatWs.on('typing', (event: any) => {
      if (event.user_id !== user?.id) {
        setTypingUser(event.user_name)
        setIsTyping(event.is_typing)
        
        if (typingTimeoutRef.current) {
          clearTimeout(typingTimeoutRef.current)
        }
        
        if (event.is_typing) {
          typingTimeoutRef.current = setTimeout(() => {
            setIsTyping(false)
            setTypingUser(null)
          }, 3000)
        }
      }
    })

    chatWs.connect().then(() => {
      setWs(chatWs)
    }).catch(console.error)

    return () => {
      chatWs.disconnect()
    }
  }, [roomId, token, user?.id])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (ws) {
        ws.send({
          type: 'send_message',
          content,
          message_type: 'TEXT',
        })
      } else {
        // Fallback to REST API
        const response = await apiClient.post('/chat/messages/', {
          room: roomId,
          content,
          message_type: 'TEXT',
        })
        return response.data
      }
    },
    onSuccess: () => {
      setMessage('')
      refetch()
    },
  })

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    sendMessageMutation.mutate(message)
  }

  const handleTyping = () => {
    if (ws && message.trim()) {
      ws.send({
        type: 'typing',
        is_typing: true,
      })
    }
  }

  const handleStopTyping = () => {
    if (ws) {
      ws.send({
        type: 'typing',
        is_typing: false,
      })
    }
  }

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg border p-3 cursor-pointer" onClick={onMinimize}>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm font-medium">Chat</span>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-lg border flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h3 className="font-semibold">Chat</h3>
          {orderId && <p className="text-sm text-gray-500">Order #{orderId}</p>}
        </div>
        <div className="flex items-center gap-2">
          {onMinimize && (
            <Button variant="ghost" size="sm" onClick={onMinimize}>
              −
            </Button>
          )}
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isOwnMessage = msg.sender === user?.id
          return (
            <div
              key={msg.id}
              className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] ${isOwnMessage ? 'order-2' : 'order-1'}`}>
                {!isOwnMessage && (
                  <div className="flex items-center gap-2 mb-1">
                    {msg.sender_photo ? (
                      <img
                        src={msg.sender_photo}
                        alt={msg.sender_name}
                        className="w-6 h-6 rounded-full"
                      />
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                        {msg.sender_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className="text-xs font-medium">{msg.sender_name}</span>
                  </div>
                )}
                <div
                  className={`rounded-lg p-3 ${
                    isOwnMessage
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {msg.image_url && (
                    <img
                      src={msg.image_url}
                      alt="Chat image"
                      className="max-w-full rounded mb-2"
                    />
                  )}
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className={`text-xs mt-1 ${isOwnMessage ? 'text-primary-100' : 'text-gray-500'}`}>
                    {formatDate(msg.created_at)}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
        {isTyping && typingUser && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <p className="text-sm text-gray-500 italic">{typingUser} is typing...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 border-t">
        <div className="flex items-center gap-2">
          <Input
            value={message}
            onChange={(e) => {
              setMessage(e.target.value)
              handleTyping()
            }}
            onBlur={handleStopTyping}
            placeholder="Type a message..."
            className="flex-1"
          />
          <Button type="submit" disabled={!message.trim() || sendMessageMutation.isPending}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}

