import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
// import { Textarea } from '@/packages/ui/components/textarea' // Using textarea element directly
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Send, CheckCircle, Clock, XCircle } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatDate } from '@/packages/utils/format'

const statusColors: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-700',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-700',
  RESOLVED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [newMessage, setNewMessage] = useState('')

  const { data: ticket, isLoading } = useQuery({
    queryKey: ['support-ticket', id],
    queryFn: async () => {
      const response = await apiClient.get(`/support/tickets/${id}/`)
      return response.data
    },
  })

  const addMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await apiClient.post(`/support/tickets/${id}/add_message/`, { message })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support-ticket', id] })
      setNewMessage('')
    },
  })

  const closeTicketMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/support/tickets/${id}/close/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support-ticket', id] })
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] })
    },
  })

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMessage.trim()) {
      addMessageMutation.mutate(newMessage)
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!ticket) {
    return <div>Ticket not found</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <Button variant="outline" onClick={() => navigate('/support')} className="mb-4">
          ← Back to Support
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{ticket.subject}</h1>
            <div className="flex items-center gap-2">
              <Badge className={statusColors[ticket.status] || ''}>
                {ticket.status.replace('_', ' ')}
              </Badge>
              <span className="text-gray-600">Ticket #{ticket.ticket_number}</span>
            </div>
          </div>
          {ticket.status !== 'CLOSED' && (
            <Button
              variant="outline"
              onClick={() => closeTicketMutation.mutate()}
              disabled={closeTicketMutation.isPending}
            >
              Close Ticket
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Conversation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-6">
                {/* Initial ticket description */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold">{ticket.user_name || ticket.user_email}</span>
                    <span className="text-xs text-gray-500">{formatDate(ticket.created_at)}</span>
                  </div>
                  <p className="text-gray-700">{ticket.description}</p>
                </div>

                {/* Messages */}
                {ticket.messages && ticket.messages.length > 0 && (
                  <>
                    {ticket.messages.map((msg: any) => (
                      <div
                        key={msg.id}
                        className={`p-4 rounded-lg ${
                          msg.is_internal ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold">{msg.user_name || msg.user_email}</span>
                          {msg.is_internal && (
                            <Badge variant="outline" className="text-xs">
                              Internal Note
                            </Badge>
                          )}
                          <span className="text-xs text-gray-500">{formatDate(msg.created_at)}</span>
                        </div>
                        <p className="text-gray-700">{msg.message}</p>
                      </div>
                    ))}
                  </>
                )}
              </div>

              {/* Add message form */}
              {ticket.status !== 'CLOSED' && (
                <form onSubmit={handleSendMessage} className="space-y-2">
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    rows={3}
                    className="w-full p-3 border rounded-lg"
                  />
                  <Button type="submit" disabled={addMessageMutation.isPending || !newMessage.trim()}>
                    <Send className="w-4 h-4 mr-2" />
                    {addMessageMutation.isPending ? 'Sending...' : 'Send Message'}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ticket Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm text-gray-600">Category</div>
                <div className="font-medium">{ticket.category.replace('_', ' ')}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Status</div>
                <Badge className={statusColors[ticket.status] || ''}>
                  {ticket.status.replace('_', ' ')}
                </Badge>
              </div>
              <div>
                <div className="text-sm text-gray-600">Priority</div>
                <div className="font-medium">{ticket.priority}</div>
              </div>
              {ticket.order_number && (
                <div>
                  <div className="text-sm text-gray-600">Related Order</div>
                  <Button
                    variant="link"
                    className="p-0 h-auto"
                    onClick={() => navigate(`/orders/${ticket.order}`)}
                  >
                    {ticket.order_number}
                  </Button>
                </div>
              )}
              {ticket.assigned_to_email && (
                <div>
                  <div className="text-sm text-gray-600">Assigned To</div>
                  <div className="font-medium">{ticket.assigned_to_email}</div>
                </div>
              )}
              {ticket.resolved_at && (
                <div>
                  <div className="text-sm text-gray-600">Resolved At</div>
                  <div className="font-medium">{formatDate(ticket.resolved_at)}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

