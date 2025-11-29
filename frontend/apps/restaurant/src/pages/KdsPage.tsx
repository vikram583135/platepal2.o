import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Clock, ChefHat, Package, CheckCircle2, AlertCircle } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useRestaurantStore } from '../stores/restaurantStore'

interface KDSBoard {
  new: any[]
  preparing: any[]
  ready: any[]
  completed: any[]
}

export default function KDSPage() {
  const queryClient = useQueryClient()
  const { selectedRestaurantId } = useRestaurantStore()
  const [view, setView] = useState<'new' | 'preparing' | 'ready' | 'completed'>('new')
  const [fullscreen, setFullscreen] = useState(false)

  const { data: board, isLoading, error } = useQuery<KDSBoard>({
    queryKey: ['kds-board', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/orders/orders/kds_board/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchInterval: 5000, // Refresh every 5 seconds (reduced to avoid 429)
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  const startPreparingMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/start_preparing/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kds-board', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to start preparing order:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to start preparing'
      alert(errorMsg)
    },
  })

  const markReadyMutation = useMutation({
    mutationFn: async (orderId: number) => {
      return apiClient.post(`/orders/orders/${orderId}/mark_ready/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kds-board', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to mark order as ready:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to mark as ready'
      alert(errorMsg)
    },
  })

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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      switch (e.key.toLowerCase()) {
        case 'a':
        case 's':
          // Accept/Start preparing
          if (view === 'new' && board?.new?.[0]) {
            startPreparingMutation.mutate(board.new[0].id)
          }
          break
        case 'd':
          // Done/Ready
          if (view === 'preparing' && board?.preparing?.[0]) {
            markReadyMutation.mutate(board.preparing[0].id)
          }
          break
        case 'f':
          // Toggle fullscreen
          setFullscreen((prev) => !prev)
          break
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [view, board, startPreparingMutation, markReadyMutation])

  // Audio alert for new orders
  useEffect(() => {
    if (board?.new && board.new.length > 0) {
      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZkDkI')
      audio.play().catch(() => { }) // Ignore errors
    }
  }, [board?.new?.length])

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view KDS</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-zomato-gray">Loading KDS...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load KDS board</p>
          <p className="text-zomato-gray text-sm">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const currentOrders = board?.[view] || []

  return (
    <div className={`min-h-screen page-background ${fullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-zomato-dark">Kitchen Display System</h1>
              <p className="text-sm text-zomato-gray mt-1">Real-time order management</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                {(['new', 'preparing', 'ready', 'completed'] as const).map((v) => (
                  <Button
                    key={v}
                    onClick={() => setView(v)}
                    className={`${view === v
                        ? 'bg-zomato-red text-white'
                        : 'bg-white text-zomato-gray hover:bg-red-50'
                      }`}
                  >
                    {v.charAt(0).toUpperCase() + v.slice(1)} ({board?.[v]?.length || 0})
                  </Button>
                ))}
              </div>
              <Button
                onClick={() => setFullscreen(!fullscreen)}
                className="bg-zomato-red hover:bg-zomato-darkRed text-white"
              >
                {fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2">
        <div className="max-w-7xl mx-auto text-xs text-yellow-800">
          <strong>Shortcuts:</strong> A/S = Accept/Start, D = Done/Ready, F = Fullscreen
        </div>
      </div>

      {/* KDS Board */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {currentOrders.map((order: any) => {
            const timeElapsed = getTimeElapsed(order.created_at)
            const isUrgent = timeElapsed > 20

            return (
              <Card
                key={order.id}
                className={`bg-white ${isUrgent ? 'border-l-4 border-l-red-500 bg-red-50' : ''
                  }`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-2xl font-bold text-zomato-dark">
                          #{order.order_number}
                        </span>
                        {isUrgent && (
                          <span className="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded animate-pulse">
                            RUSH
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-zomato-gray">{formatTime(order.created_at)}</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-orange-600">
                        <Clock className="h-4 w-4" />
                        <span className="text-lg font-bold">{timeElapsed}m</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 mb-4">
                    {order.items?.map((item: any) => (
                      <div
                        key={item.id}
                        className="p-3 bg-red-50 rounded-lg border-l-4 border-l-zomato-red"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-semibold text-zomato-dark">{item.name}</p>
                            <p className="text-sm text-zomato-gray">Qty: {item.quantity}</p>
                            {item.selected_modifiers?.length > 0 && (
                              <div className="mt-2 text-xs text-zomato-gray">
                                {item.selected_modifiers.map((mod: any) => (
                                  <div key={mod.name}>+ {mod.name}</div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {order.special_instructions && (
                    <div className="mb-4 p-3 bg-yellow-50 border-l-4 border-l-yellow-500 rounded">
                      <p className="text-sm font-medium text-yellow-900">Special Instructions:</p>
                      <p className="text-sm text-yellow-800 mt-1">{order.special_instructions}</p>
                    </div>
                  )}

                  <div className="flex gap-2">
                    {view === 'new' && (
                      <Button
                        onClick={() => startPreparingMutation.mutate(order.id)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-lg py-3"
                      >
                        <ChefHat className="h-5 w-5 mr-2" />
                        Start (S)
                      </Button>
                    )}
                    {view === 'preparing' && (
                      <Button
                        onClick={() => markReadyMutation.mutate(order.id)}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white text-lg py-3"
                      >
                        <CheckCircle2 className="h-5 w-5 mr-2" />
                        Ready (D)
                      </Button>
                    )}
                    {view === 'ready' && (
                      <div className="flex-1 bg-green-100 text-green-800 text-center py-3 rounded-lg font-semibold">
                        <Package className="h-5 w-5 inline mr-2" />
                        Ready for Pickup
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {currentOrders.length === 0 && (
          <div className="text-center py-16">
            <p className="text-xl text-zomato-gray">No orders in {view} status</p>
          </div>
        )}
      </div>
    </div>
  )
}
