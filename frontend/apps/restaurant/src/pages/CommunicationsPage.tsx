import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'
import { AlertCircle, MessageSquare, Phone, Package, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/packages/utils/cn'

const PREDEFINED_MESSAGES = [
  { label: 'Order ready', text: 'Your order is ready for pickup!' },
  { label: 'On the way', text: 'Your order is on the way. Estimated delivery in 15-20 minutes.' },
  { label: 'Delayed', text: 'We apologize for the delay. Your order will be ready shortly.' },
  { label: 'Out of stock', text: 'We apologize, but one of your items is currently out of stock. We can offer a replacement or refund.' },
  { label: 'Thank you', text: 'Thank you for your order! We hope you enjoy your meal.' },
  { label: 'Apology', text: 'We sincerely apologize for any inconvenience. Please let us know how we can make it right.' },
]

export default function CommunicationsPage() {
  const { selectedRestaurantId } = useRestaurantStore()
  const queryClient = useQueryClient()
  const [activeRoomId, setActiveRoomId] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [showPredefined, setShowPredefined] = useState(false)

  const roomsQuery = useQuery({
    queryKey: ['chat-rooms', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/chat/rooms/', {
        params: { restaurant: selectedRestaurantId },
      })
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || [])
    },
    enabled: Boolean(selectedRestaurantId),
  })

  // Set active room after data loads
  useEffect(() => {
    if (!activeRoomId && roomsQuery.data && roomsQuery.data.length > 0) {
      setActiveRoomId(roomsQuery.data[0].id)
    }
  }, [activeRoomId, roomsQuery.data])

  const messagesQuery = useQuery({
    queryKey: ['chat-messages', activeRoomId],
    queryFn: async () => {
      if (!activeRoomId) {
        throw new Error('No room selected')
      }
      const response = await apiClient.get('/chat/messages/', {
        params: { room: activeRoomId },
      })
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || [])
    },
    enabled: Boolean(activeRoomId),
    refetchInterval: 15000, // Reduced to avoid 429
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  const sendMessage = useMutation({
    mutationFn: async (content?: string) => {
      if (!activeRoomId) {
        throw new Error('No room selected')
      }
      await apiClient.post('/chat/messages/', {
        room: activeRoomId,
        content: (content || message).trim(),
      })
    },
    onSuccess: () => {
      setMessage('')
      setShowPredefined(false)
      queryClient.invalidateQueries({ queryKey: ['chat-messages', activeRoomId] })
    },
    onError: (error: any) => {
      console.error('Failed to send message:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to send message'
      alert(errorMsg)
    },
  })

  const formatTime = (dateString: string | undefined | null) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return 'N/A'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    }
    return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
  }

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view communications</p>
        </div>
      </div>
    )
  }

  if (roomsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading communications...</p>
      </div>
    )
  }

  if (roomsQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load communications</p>
          <p className="text-zomato-gray text-sm">
            {roomsQuery.error instanceof Error ? roomsQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const rooms = roomsQuery.data || []
  const messages = messagesQuery.data || []

  const activeRoom = rooms.find((r: any) => r.id === activeRoomId)

  return (
    <div className="min-h-screen bg-zomato-lightGray p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zomato-dark">Communications Center</h1>
        <p className="text-zomato-gray mt-1">Handle customer & rider chats, send predefined messages</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Active Threads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
            {rooms.length > 0 ? (
              rooms.map((room: any) => {
                const isActive = room.id === activeRoomId
                const unreadCount = room.unread_count || 0
                return (
                  <button
                    key={room.id}
                    className={cn(
                      'w-full rounded-lg border px-3 py-3 text-left transition-colors',
                      isActive
                        ? 'border-zomato-red bg-zomato-red/10 text-zomato-dark'
                        : 'border-gray-200 hover:bg-gray-50'
                    )}
                    onClick={() => setActiveRoomId(room.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <MessageSquare className="h-4 w-4 text-zomato-gray" />
                          <span className="font-semibold text-sm">
                            {room.room_type === 'ORDER' && room.order_number
                              ? `Order #${room.order_number}`
                              : room.customer_name || 'Customer'}
                          </span>
                        </div>
                        {room.last_message && (
                          <p className="text-xs text-zomato-gray truncate">{room.last_message.content}</p>
                        )}
                        {room.last_message_at && (
                          <p className="text-xs text-zomato-gray mt-1">
                            {formatDate(room.last_message_at)} {formatTime(room.last_message_at)}
                          </p>
                        )}
                      </div>
                      {unreadCount > 0 && (
                        <span className="bg-zomato-red text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                          {unreadCount}
                        </span>
                      )}
                    </div>
                  </button>
                )
              })
            ) : (
              <p className="text-xs text-zomato-gray text-center py-8">No active chats</p>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">
                  {activeRoom
                    ? activeRoom.room_type === 'ORDER' && activeRoom.order_number
                      ? `Order #${activeRoom.order_number}`
                      : `Chat with ${activeRoom.customer_name || 'Customer'}`
                    : 'Select a conversation'}
                </CardTitle>
                {activeRoom?.order_number && (
                  <p className="text-sm text-zomato-gray mt-1">Order chat thread</p>
                )}
              </div>
              {activeRoomId && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowPredefined(!showPredefined)}
                >
                  <MessageSquare className="h-4 w-4 mr-1" />
                  Quick Messages
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {showPredefined && (
              <div className="mb-4 p-4 bg-zomato-lightGray rounded-lg">
                <p className="text-xs font-semibold uppercase tracking-wide text-zomato-gray mb-2">
                  Predefined Messages
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {PREDEFINED_MESSAGES.map((msg, idx) => (
                    <Button
                      key={idx}
                      size="sm"
                      variant="outline"
                      className="text-xs justify-start"
                      onClick={() => sendMessage.mutate(msg.text)}
                    >
                      {msg.label}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto mb-4">
              {messages.length > 0 ? (
                messages.map((msg: any, idx: number) => {
                  const isMine = msg.sender_email === queryClient.getQueryData(['auth-user'])?.email || msg.is_mine
                  const showDate =
                    idx === 0 ||
                    new Date(msg.created_at).toDateString() !==
                      new Date(messages[idx - 1].created_at).toDateString()

                  return (
                    <div key={msg.id}>
                      {showDate && (
                        <div className="text-center text-xs text-zomato-gray my-3">
                          {formatDate(msg.created_at)}
                        </div>
                      )}
                      <div
                        className={cn(
                          'rounded-lg px-4 py-2 max-w-[80%]',
                          isMine
                            ? 'ml-auto bg-zomato-red text-white'
                            : 'bg-white border border-gray-200 text-zomato-dark'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold">{msg.sender_name || 'Anonymous'}</span>
                          <span className="text-xs opacity-70">{formatTime(msg.created_at)}</span>
                        </div>
                        <p className="text-sm">{msg.content}</p>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-12 text-zomato-gray">
                  {activeRoomId ? 'No messages yet. Start the conversation!' : 'Select a conversation to view messages.'}
                </div>
              )}
            </div>

            {activeRoomId && (
              <div className="flex gap-2">
                <Input
                  placeholder="Type your message…"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && message.trim()) {
                      sendMessage.mutate()
                    }
                  }}
                  className="flex-1"
                />
                <Button
                  disabled={!message.trim() || sendMessage.isPending}
                  onClick={() => sendMessage.mutate()}
                  className="bg-zomato-red hover:bg-zomato-darkRed text-white"
                >
                  {sendMessage.isPending ? 'Sending...' : 'Send'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


