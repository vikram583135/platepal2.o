import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import {
  Clock,
  MapPin,
  Phone,
  PhoneCall,
  User,
  Package,
  CheckCircle2,
  XCircle,
  ChefHat,
  AlertCircle,
  TimerReset,
  MessageCircle,
  Flame,
  GitMerge,
  Printer,
  AlertTriangle,
} from 'lucide-react'
import { useState, useEffect, useMemo } from 'react'
import { useRestaurantStore } from '../stores/restaurantStore'
import { cn } from '@/packages/utils/cn'

interface OrderQueue {
  new: any[]
  accepted: any[]
  preparing: any[]
  ready: any[]
  assigned: any[]
  out_for_delivery: any[]
  completed: any[]
  cancelled: any[]
  metrics: any
}

export default function OrdersPage() {
  const queryClient = useQueryClient()
  const { selectedRestaurantId } = useRestaurantStore()
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [prepMinutes, setPrepMinutes] = useState(20)
  const [noteText, setNoteText] = useState('')
  const [priorityTag, setPriorityTag] = useState<'NORMAL' | 'RUSH' | 'VIP'>('NORMAL')
  const [combineTarget, setCombineTarget] = useState('')
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const { data: queue, isLoading, error } = useQuery<OrderQueue>({
    queryKey: ['restaurant-orders-queue', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/orders/orders/queue/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      // Normalize response structure
      const data = response.data
      if (!data) {
        return {
          new: [],
          accepted: [],
          preparing: [],
          ready: [],
          assigned: [],
          out_for_delivery: [],
          completed: [],
          cancelled: [],
          metrics: {},
        }
      }
      return data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchInterval: 10000, // Refresh every 10 seconds (reduced to avoid 429)
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
    retry: 1,
  })

  const acceptMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/accept/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Order accepted successfully.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to accept order:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to accept order'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const declineMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/decline/`, {
        reason: 'Restaurant declined',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Order declined.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to decline order:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to decline order'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const startPreparingMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/start_preparing/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Order preparation started.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to start preparing order:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to start preparing'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const markReadyMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/mark_ready/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Order marked as ready.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to mark order as ready:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to mark as ready'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const updatePrepMutation = useMutation({
    mutationFn: async ({ orderId, minutes }: { orderId: number; minutes: number }) => {
      return apiClient.post(`/orders/orders/${orderId}/update_prep_time/`, { minutes })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Preparation time updated successfully.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to update prep time:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update prep time'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const noteMutation = useMutation({
    mutationFn: async ({ orderId, note }: { orderId: number; note: string }) => {
      return apiClient.post(`/orders/orders/${orderId}/add_kitchen_note/`, { note })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Kitchen note saved.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to save kitchen note:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save note'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const priorityMutation = useMutation({
    mutationFn: async ({ orderId, priority }: { orderId: number; priority: string }) => {
      return apiClient.post(`/orders/orders/${orderId}/mark_priority/`, { priority_tag: priority })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Priority updated.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to update priority:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update priority'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const combineMutation = useMutation({
    mutationFn: async ({ orderId, target }: { orderId: number; target: number }) => {
      return apiClient.post(`/orders/orders/${orderId}/combine_with/`, { target_order_id: target })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Orders combined successfully.')
      setCombineTarget('')
      setSelectedOrder(null)
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to combine orders:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to combine orders'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  const printMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/print_docket/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders-queue', selectedRestaurantId] })
      setActionMessage('Print count updated.')
      setTimeout(() => setActionMessage(null), 3000)
    },
    onError: (error: any) => {
      console.error('Failed to print docket:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to print docket'
      setActionMessage(`Error: ${errorMsg}`)
      setTimeout(() => setActionMessage(null), 5000)
    },
  })

  useEffect(() => {
    if (selectedOrder) {
      setPrepMinutes(selectedOrder.prep_time_override_minutes || selectedOrder.estimated_preparation_time || 20)
      setNoteText(selectedOrder.kitchen_notes || '')
      setPriorityTag(selectedOrder.priority_tag || 'NORMAL')
      setCombineTarget('')
    }
  }, [selectedOrder])

  const combineCandidates = useMemo(() => {
    if (!queue || !selectedOrder) return []
    const relevantPools: Array<keyof OrderQueue> = ['new', 'accepted', 'preparing']
    const sameAddressOrders: any[] = []
    relevantPools.forEach((pool) => {
      queue[pool]?.forEach((order: any) => {
        if (
          order.id !== selectedOrder.id &&
          order.delivery_address?.id &&
          order.delivery_address?.id === selectedOrder.delivery_address?.id
        ) {
          sameAddressOrders.push(order)
        }
      })
    })
    return sameAddressOrders
  }, [queue, selectedOrder])

  const formatCurrency = (amount: number | undefined | null) => {
    if (amount === undefined || amount === null || isNaN(amount)) {
      return '₹0'
    }
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount)
  }

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

  const getTimeElapsed = (dateString: string | undefined | null) => {
    if (!dateString) return 0
    try {
      const now = new Date()
      const then = new Date(dateString)
      if (isNaN(then.getTime())) return 0
      const diff = Math.floor((now.getTime() - then.getTime()) / 1000 / 60)
      return Math.max(0, diff)
    } catch {
      return 0
    }
  }

  const OrderCard = ({ order, status }: { order: any; status: string }) => {
    if (!order) return null
    const timeElapsed = getTimeElapsed(order.created_at)
    const isUrgent = timeElapsed > (order.estimated_preparation_time || 20)
    const priority = order.priority_tag || 'NORMAL'
    const priorityColors: Record<string, string> = {
      RUSH: 'bg-red-100 text-red-700 border-red-300',
      VIP: 'bg-amber-100 text-amber-700 border-amber-300',
      NORMAL: 'bg-slate-100 text-slate-700 border-slate-300',
    }

    return (
      <Card
        className={`mb-4 cursor-pointer hover:shadow-lg transition-shadow ${
          isUrgent ? 'border-l-4 border-l-red-500 bg-red-50' : 'bg-white'
        }`}
        onClick={() => setSelectedOrder(order)}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-zomato-dark">#{order.order_number}</span>
                {priority !== 'NORMAL' && (
                  <span className={cn('text-xs font-semibold px-2 py-0.5 rounded border', priorityColors[priority])}>
                    {priority}
                  </span>
                )}
                {order.sla_breached && (
                  <span className="bg-red-600 text-white text-xs font-semibold px-2 py-0.5 rounded animate-pulse">
                    SLA
                  </span>
                )}
                {isUrgent && !order.sla_breached && (
                  <span className="bg-orange-500 text-white text-xs font-semibold px-2 py-0.5 rounded">
                    URGENT
                  </span>
                )}
              </div>
              <p className="text-xs text-zomato-gray mt-1">{formatTime(order.created_at || order.order_created_at)}</p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-zomato-dark">{formatCurrency(order.total_amount)}</p>
              <p className="text-xs text-zomato-gray">{order.items?.length || order.order_items?.length || 0} items</p>
            </div>
          </div>

          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-zomato-gray" />
              <span className="text-zomato-dark">
                {order.customer?.first_name} {order.customer?.last_name}
              </span>
            </div>
            {order.delivery_address && (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-zomato-gray" />
                <span className="text-zomato-gray text-xs truncate">
                  {order.delivery_address.street}, {order.delivery_address.city}
                </span>
              </div>
            )}
            {order.customer?.phone && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-zomato-gray" />
                <span className="text-zomato-gray text-xs">{order.customer.phone}</span>
              </div>
            )}
          </div>

          {order.special_instructions && (
            <div className="mt-3 p-2 bg-yellow-50 rounded text-xs text-zomato-dark">
              <strong>Note:</strong> {order.special_instructions}
            </div>
          )}

          <div className="mt-4 flex gap-2">
            {status === 'new' && (
              <>
                <Button
                  onClick={(e) => {
                    e.stopPropagation()
                    acceptMutation.mutate(order.id)
                  }}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm"
                >
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                  Accept
                </Button>
                <Button
                  onClick={(e) => {
                    e.stopPropagation()
                    declineMutation.mutate(order.id)
                  }}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white text-sm"
                >
                  <XCircle className="h-4 w-4 mr-1" />
                  Decline
                </Button>
              </>
            )}
            {status === 'accepted' && (
              <Button
                onClick={(e) => {
                  e.stopPropagation()
                  startPreparingMutation.mutate(order.id)
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm"
              >
                <ChefHat className="h-4 w-4 mr-1" />
                Start Preparing
              </Button>
            )}
            {status === 'preparing' && (
              <Button
                onClick={(e) => {
                  e.stopPropagation()
                  markReadyMutation.mutate(order.id)
                }}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm"
              >
                <Package className="h-4 w-4 mr-1" />
                Mark Ready
              </Button>
            )}
          </div>

          <div className="mt-2 flex items-center gap-3 text-xs text-zomato-gray">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {timeElapsed} min elapsed
            </div>
            {order.print_count > 0 && (
              <div className="flex items-center gap-1">
                <Printer className="h-3 w-3" />
                {order.print_count} prints
              </div>
            )}
            {order.kitchen_notes && (
              <div className="flex items-center gap-1">
                <MessageCircle className="h-3 w-3" />
                Note
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  const OrderDetailModal = ({ order, onClose }: { order: any; onClose: () => void }) => {
    if (!order) return null

    const timeline = [
      { label: 'Placed', value: order.created_at },
      { label: 'Accepted', value: order.accepted_at },
      { label: 'Preparing', value: order.preparing_at },
      { label: 'Ready', value: order.ready_at },
      { label: 'Picked', value: order.picked_up_at },
      { label: 'Delivered', value: order.delivered_at },
    ].filter((entry) => entry.value)

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <Card className="bg-white max-w-5xl w-full max-h-[90vh] overflow-y-auto">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-zomato-gray">Order Detail</p>
                <h2 className="text-2xl font-bold text-zomato-dark">#{order.order_number}</h2>
              </div>
              <Button onClick={onClose} variant="ghost" className="text-zomato-gray">
                ✕
              </Button>
            </div>

            {actionMessage && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                {actionMessage}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <h3 className="font-semibold text-zomato-dark mb-2">Customer</h3>
                  <p className="text-sm text-zomato-gray">
                    {order.customer?.first_name} {order.customer?.last_name}
                  </p>
                  {order.customer?.phone && (
                    <div className="mt-2 flex gap-2">
                      <Button
                        asChild
                        size="sm"
                        variant="outline"
                        className="text-xs"
                      >
                        <a href={`tel:${order.customer.phone}`}>
                          <PhoneCall className="h-3 w-3 mr-1" />
                          Call
                        </a>
                      </Button>
                      {order.delivery_address && (
                        <Button
                          asChild
                          size="sm"
                          variant="outline"
                          className="text-xs"
                        >
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                              `${order.delivery_address.street}, ${order.delivery_address.city}`
                            )}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <MapPin className="h-3 w-3 mr-1" />
                            Map
                          </a>
                        </Button>
                      )}
                    </div>
                  )}
                  {order.delivery_address && (
                    <p className="text-sm text-zomato-gray mt-2">
                      {order.delivery_address.street}, {order.delivery_address.city},{' '}
                      {order.delivery_address.state} {order.delivery_address.postal_code}
                    </p>
                  )}
                </div>

              <div>
                <h3 className="font-semibold text-zomato-dark mb-2">Items</h3>
                <div className="space-y-2">
                  {order.items?.map((item: any) => (
                    <div key={item.id} className="flex justify-between p-2 bg-red-50 rounded border border-red-100">
                      <div>
                        <p className="text-sm font-medium text-zomato-dark">{item.name}</p>
                        <p className="text-xs text-zomato-gray">Qty: {item.quantity}</p>
                      </div>
                      <p className="text-sm font-semibold text-zomato-dark">
                        {formatCurrency(item.total_price)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-zomato-dark mb-2">Payment</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zomato-gray">Subtotal:</span>
                    <span className="text-zomato-dark">{formatCurrency(order.subtotal || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zomato-gray">Tax:</span>
                    <span className="text-zomato-dark">{formatCurrency(order.tax_amount || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zomato-gray">Delivery Fee:</span>
                    <span className="text-zomato-dark">{formatCurrency(order.delivery_fee || 0)}</span>
                  </div>
                  {(order.discount_amount || 0) > 0 && (
                    <div className="flex justify-between">
                      <span className="text-zomato-gray">Discount:</span>
                      <span className="text-green-600">-{formatCurrency(order.discount_amount || 0)}</span>
                    </div>
                  )}
                  <div className="flex justify-between font-bold text-lg pt-2 border-t">
                    <span className="text-zomato-dark">Total:</span>
                    <span className="text-zomato-red">{formatCurrency(order.total_amount)}</span>
                  </div>
                </div>
              </div>

                {timeline.length > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                    <h3 className="font-semibold text-zomato-dark mb-2">Timeline</h3>
                    <div className="space-y-1 text-sm">
                      {timeline.map((entry) => (
                        <div key={entry.label} className="flex justify-between">
                          <span className="text-zomato-gray">{entry.label}</span>
                          <span className="text-zomato-dark">{formatTime(entry.value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {order.special_instructions && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h3 className="font-semibold text-yellow-900 mb-2">Special Instructions</h3>
                    <p className="text-sm text-yellow-800">{order.special_instructions}</p>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                {order.sla_breached && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      <h3 className="font-semibold text-red-900">SLA Breach</h3>
                    </div>
                    <p className="text-sm text-red-800">
                      {order.sla_breach_reason || 'Order exceeded preparation time threshold'}
                    </p>
                  </div>
                )}

                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center gap-2 mb-3">
                    <TimerReset className="h-4 w-4 text-zomato-dark" />
                    <h3 className="font-semibold text-zomato-dark">Modify Prep Time</h3>
                  </div>
                  <input
                    type="range"
                    min={5}
                    max={90}
                    step={5}
                    value={prepMinutes}
                    onChange={(e) => setPrepMinutes(Number(e.target.value))}
                    className="w-full mb-2"
                  />
                  <div className="text-sm text-zomato-gray mb-3">{prepMinutes} minutes</div>
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => updatePrepMutation.mutate({ orderId: order.id, minutes: prepMinutes })}
                    disabled={updatePrepMutation.isPending}
                  >
                    Save Prep Time
                  </Button>
                </div>

                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center gap-2 mb-3">
                    <MessageCircle className="h-4 w-4 text-zomato-dark" />
                    <h3 className="font-semibold text-zomato-dark">Kitchen Notes</h3>
                  </div>
                  <textarea
                    className="w-full p-2 border border-gray-300 rounded text-sm mb-3"
                    rows={3}
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Add internal cooking notes..."
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => noteMutation.mutate({ orderId: order.id, note: noteText })}
                    disabled={noteMutation.isPending}
                  >
                    Save Note
                  </Button>
                </div>

                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Flame className="h-4 w-4 text-zomato-dark" />
                    <h3 className="font-semibold text-zomato-dark">Priority</h3>
                  </div>
                  <div className="flex gap-2 mb-3">
                    {['NORMAL', 'RUSH', 'VIP'].map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => setPriorityTag(tag as any)}
                        className={cn(
                          'px-3 py-1 rounded text-xs font-semibold',
                          priorityTag === tag
                            ? 'bg-zomato-red text-white'
                            : 'bg-white border border-gray-300 text-zomato-gray'
                        )}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => priorityMutation.mutate({ orderId: order.id, priority: priorityTag })}
                    disabled={priorityMutation.isPending}
                  >
                    Update Priority
                  </Button>
                </div>

                {combineCandidates.length > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                    <div className="flex items-center gap-2 mb-3">
                      <GitMerge className="h-4 w-4 text-zomato-dark" />
                      <h3 className="font-semibold text-zomato-dark">Combine Orders</h3>
                    </div>
                    <select
                      className="w-full p-2 border border-gray-300 rounded text-sm mb-3"
                      value={combineTarget}
                      onChange={(e) => setCombineTarget(e.target.value)}
                    >
                      <option value="">Select order to combine with</option>
                      {combineCandidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          #{candidate.order_number} - {formatCurrency(candidate.total_amount)}
                        </option>
                      ))}
                    </select>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        combineMutation.mutate({ orderId: order.id, target: Number(combineTarget) })
                      }
                      disabled={!combineTarget || combineMutation.isPending}
                    >
                      Combine Orders
                    </Button>
                  </div>
                )}

                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center gap-2 mb-3">
                    <Printer className="h-4 w-4 text-zomato-dark" />
                    <h3 className="font-semibold text-zomato-dark">Print & Notify</h3>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full mb-2"
                    onClick={() => printMutation.mutate(order.id)}
                    disabled={printMutation.isPending}
                  >
                    Print Docket ({order.print_count || 0} prints)
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    asChild
                  >
                    <a href="/communications">Open Communications</a>
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view orders</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-zomato-gray">Loading orders...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load orders</p>
          <p className="text-zomato-gray text-sm">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const columns = [
    { key: 'new', title: 'New Orders', orders: queue?.new || [], color: 'bg-yellow-100 border-yellow-500' },
    {
      key: 'accepted',
      title: 'Accepted',
      orders: queue?.accepted || [],
      color: 'bg-blue-100 border-blue-500',
    },
    {
      key: 'preparing',
      title: 'Preparing',
      orders: queue?.preparing || [],
      color: 'bg-purple-100 border-purple-500',
    },
    {
      key: 'ready',
      title: 'Ready',
      orders: queue?.ready || [],
      color: 'bg-green-100 border-green-500',
    },
    {
      key: 'assigned',
      title: 'Assigned',
      orders: queue?.assigned || [],
      color: 'bg-indigo-100 border-indigo-500',
    },
    {
      key: 'out_for_delivery',
      title: 'Out for Delivery',
      orders: queue?.out_for_delivery || [],
      color: 'bg-teal-100 border-teal-500',
    },
  ]

  const metrics = queue?.metrics || {}
  const statCards = [
    { label: 'Pending', value: metrics.pending || 0, color: 'bg-yellow-50 border-yellow-500 text-yellow-800' },
    { label: 'Preparing', value: metrics.preparing || 0, color: 'bg-purple-50 border-purple-500 text-purple-800' },
    { label: 'Ready', value: metrics.ready || 0, color: 'bg-green-50 border-green-500 text-green-800' },
    { label: 'Out for Delivery', value: metrics.out_for_delivery || 0, color: 'bg-teal-50 border-teal-500 text-teal-800' },
    { label: 'Completed Today', value: metrics.completed_today || 0, color: 'bg-slate-50 border-slate-500 text-slate-800' },
    { label: 'Avg Prep (min)', value: metrics.avg_prep_time || 0, color: 'bg-rose-50 border-rose-500 text-rose-800' },
  ]

  return (
    <div className="min-h-screen page-background p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zomato-dark">Orders Management</h1>
        <p className="text-zomato-gray mt-1">Manage and track all your orders</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {statCards.map((stat) => (
          <div key={stat.label} className={cn('p-4 rounded-lg border-l-4', stat.color)}>
            <p className="text-xs uppercase tracking-wide mb-1">{stat.label}</p>
            <p className="text-2xl font-bold">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {columns.map((column) => (
          <div key={column.key} className="flex flex-col">
            <div className={`${column.color} border-l-4 p-3 rounded-t-lg`}>
              <h2 className="font-semibold text-zomato-dark">{column.title}</h2>
              <p className="text-sm text-zomato-gray">{column.orders.length} orders</p>
            </div>
            <div className="bg-white rounded-b-lg p-3 flex-1 overflow-y-auto max-h-[calc(100vh-200px)]">
              {column.orders.map((order) => (
                <OrderCard key={order.id} order={order} status={column.key} />
              ))}
              {column.orders.length === 0 && (
                <div className="text-center py-8 text-zomato-gray text-sm">No orders</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedOrder && (
        <OrderDetailModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />
      )}
    </div>
  )
}
