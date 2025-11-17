import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/packages/ui/components/dialog'
// Using native HTML elements
import { MessageSquare, Phone, Ticket, Send, Bot, User, CheckCircle, Clock, XCircle } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatDate } from '@/packages/utils/format'
import { useNavigate } from 'react-router-dom'

const statusColors: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-700',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-700',
  RESOLVED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
}

const priorityColors: Record<string, string> = {
  LOW: 'bg-gray-100 text-gray-700',
  MEDIUM: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  URGENT: 'bg-red-100 text-red-700',
}

export default function SupportPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showTicketModal, setShowTicketModal] = useState(false)
  const [showChatbot, setShowChatbot] = useState(false)
  const [chatbotMessage, setChatbotMessage] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [chatHistory, setChatHistory] = useState<any[]>([])
  const chatEndRef = useRef<HTMLDivElement>(null)

  const { data: tickets, isLoading: ticketsLoading } = useQuery({
    queryKey: ['support-tickets'],
    queryFn: async () => {
      const response = await apiClient.get('/support/tickets/')
      return response.data.results || response.data || []
    },
  })

  const createTicketMutation = useMutation({
    mutationFn: async (ticketData: any) => {
      const response = await apiClient.post('/support/tickets/', ticketData)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] })
      setShowTicketModal(false)
      navigate(`/support/tickets/${data.id}`)
    },
  })

  const chatbotMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await apiClient.post('/support/chatbot/message/', {
        message,
        session_id: sessionId || undefined,
      })
      return response.data
    },
    onSuccess: (data) => {
      if (!sessionId) {
        setSessionId(data.session_id)
      }
      setChatHistory((prev) => [
        ...prev,
        data.user_message,
        data.bot_message,
      ])
      setChatbotMessage('')
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    },
  })

  useEffect(() => {
    if (showChatbot && sessionId) {
      // Load chat history
      apiClient.get(`/support/chatbot/history/?session_id=${sessionId}`).then((response) => {
        setChatHistory(response.data.messages || [])
      })
    }
  }, [showChatbot, sessionId])

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    const ticketData = {
      category: formData.get('category'),
      subject: formData.get('subject'),
      description: formData.get('description'),
      order_id: formData.get('order_id') || null,
    }
    createTicketMutation.mutate(ticketData)
  }

  const handleChatbotSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (chatbotMessage.trim()) {
      chatbotMutation.mutate(chatbotMessage)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Customer Support</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowChatbot(true)}>
            <Bot className="w-4 h-4 mr-2" />
            Chat with Bot
          </Button>
          <Dialog open={showTicketModal} onOpenChange={setShowTicketModal}>
            <DialogTrigger asChild>
              <Button>
                <Ticket className="w-4 h-4 mr-2" />
                Create Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Support Ticket</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateTicket} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Category *</label>
                  <select
                    name="category"
                    required
                    className="w-full p-3 border rounded-lg"
                  >
                    <option value="">Select category</option>
                    <option value="ORDER_ISSUE">Order Issue</option>
                    <option value="PAYMENT_ISSUE">Payment Issue</option>
                    <option value="DELIVERY_ISSUE">Delivery Issue</option>
                    <option value="REFUND_REQUEST">Refund Request</option>
                    <option value="ACCOUNT_ISSUE">Account Issue</option>
                    <option value="TECHNICAL_ISSUE">Technical Issue</option>
                    <option value="FEEDBACK">Feedback</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Subject *</label>
                  <Input name="subject" placeholder="Brief description of your issue" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description *</label>
                  <textarea
                    name="description"
                    placeholder="Please provide detailed information about your issue..."
                    rows={6}
                    required
                    className="w-full p-3 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Related Order (Optional)</label>
                  <Input name="order_id" type="number" placeholder="Order ID if applicable" />
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowTicketModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createTicketMutation.isPending}>
                    {createTicketMutation.isPending ? 'Creating...' : 'Create Ticket'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setShowChatbot(true)}>
          <CardContent className="p-6 text-center">
            <Bot className="w-12 h-12 mx-auto mb-3 text-primary-600" />
            <h3 className="font-semibold mb-1">Chat with Bot</h3>
            <p className="text-sm text-gray-600">Get instant answers to common questions</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setShowTicketModal(true)}>
          <CardContent className="p-6 text-center">
            <Ticket className="w-12 h-12 mx-auto mb-3 text-primary-600" />
            <h3 className="font-semibold mb-1">Create Ticket</h3>
            <p className="text-sm text-gray-600">Submit a detailed support request</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => window.open('tel:+18001234567')}>
          <CardContent className="p-6 text-center">
            <Phone className="w-12 h-12 mx-auto mb-3 text-primary-600" />
            <h3 className="font-semibold mb-1">Call Support</h3>
            <p className="text-sm text-gray-600">Speak with our support team</p>
          </CardContent>
        </Card>
      </div>

      {/* Support Tickets */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">My Support Tickets</h2>
        {ticketsLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : tickets && tickets.length > 0 ? (
          <div className="space-y-4">
            {tickets.map((ticket: any) => (
              <Card
                key={ticket.id}
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => navigate(`/support/tickets/${ticket.id}`)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{ticket.subject}</h3>
                        <Badge className={statusColors[ticket.status] || 'bg-gray-100 text-gray-700'}>
                          {ticket.status.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline" className={priorityColors[ticket.priority] || ''}>
                          {ticket.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{ticket.category.replace('_', ' ')}</p>
                      <p className="text-gray-700">{ticket.description.substring(0, 150)}...</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Ticket #{ticket.ticket_number}</span>
                    <span>{formatDate(ticket.created_at)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Ticket className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No support tickets yet</p>
            <Button className="mt-4" onClick={() => setShowTicketModal(true)}>
              Create Your First Ticket
            </Button>
          </div>
        )}
      </div>

      {/* Chatbot Dialog */}
      <Dialog open={showChatbot} onOpenChange={setShowChatbot}>
        <DialogContent className="max-w-2xl h-[600px] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              Chat with Support Bot
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {chatHistory.length === 0 && (
              <div className="text-center py-8">
                <Bot className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">Hi! I'm your support assistant. How can I help you today?</p>
              </div>
            )}
            {chatHistory.map((msg: any, index: number) => (
              <div
                key={index}
                className={`flex ${msg.is_from_user ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    msg.is_from_user
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!msg.is_from_user && <Bot className="w-4 h-4 mt-1 flex-shrink-0" />}
                    <div className="flex-1">
                      <p className="text-sm">{msg.message}</p>
                      {msg.intent && (
                        <p className="text-xs opacity-70 mt-1">Intent: {msg.intent}</p>
                      )}
                    </div>
                    {msg.is_from_user && <User className="w-4 h-4 mt-1 flex-shrink-0" />}
                  </div>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <form onSubmit={handleChatbotSend} className="flex gap-2">
            <Input
              value={chatbotMessage}
              onChange={(e) => setChatbotMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
            />
            <Button type="submit" disabled={chatbotMutation.isPending || !chatbotMessage.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

