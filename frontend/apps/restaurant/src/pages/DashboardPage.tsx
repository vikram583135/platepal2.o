import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Bell, TrendingUp, Package, Users, DollarSign, Clock, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'
import { useRestaurantStore } from '../stores/restaurantStore'

interface DashboardMetrics {
  restaurant: {
    id: number
    name: string
    city: string
    is_online: boolean
    sla_threshold: number
  }
  orders: {
    today: number
    ongoing: number
    cancelled_today: number
    latest: any[]
  }
  sales: {
    sales_today: number
    avg_order_value: number
    payout_last_7_days: number
  }
  ratings: {
    current_rating: number
    total_reviews: number
  }
  inventory: {
    low_stock_items: number
  }
  alerts: {
    unread: number
    latest: any[]
  }
}

export default function DashboardPage() {
  const queryClient = useQueryClient()
  const { selectedRestaurantId } = useRestaurantStore()

  console.log('DashboardPage render - selectedRestaurantId:', selectedRestaurantId)

  const { data: metrics, isLoading, error } = useQuery<DashboardMetrics>({
    queryKey: ['restaurant-dashboard', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/restaurants/dashboard/overview/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      const data = response.data
      console.log('Dashboard API response:', data)
      return data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchInterval: 60000, // Refresh every 60 seconds (reduced to avoid 429)
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
    refetchOnReconnect: true,
    retry: 1,
    retryDelay: 2000,
    onError: (err) => {
      console.error('Dashboard query error:', err)
    },
  })

  const { data: alerts, error: alertsError } = useQuery({
    queryKey: ['restaurant-alerts', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/restaurants/alerts/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data.results || response.data
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const toggleOnlineMutation = useMutation({
    mutationFn: async (online: boolean) => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.post('/restaurants/dashboard/online-status/', {
        restaurant_id: selectedRestaurantId,
        is_online: online,
      })
      return response.data
    },
    onSuccess: (data) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['my-restaurants'] })
      // Update optimistically
      queryClient.setQueryData(['restaurant-dashboard', selectedRestaurantId], (old: any) => {
        if (!old) return old
        return {
          ...old,
          restaurant: {
            ...old.restaurant,
            is_online: data.is_online,
          },
        }
      })
    },
    onError: (error: any) => {
      console.error('Failed to toggle online status:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update online status'
      alert(errorMsg)
    },
  })

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

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zomato-lightGray">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view the dashboard</p>
          <p className="text-xs text-zomato-gray">Selected Restaurant ID: {selectedRestaurantId || 'None'}</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zomato-lightGray">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 rounded-full border-2 border-zomato-red border-t-transparent mx-auto mb-4"></div>
          <div className="text-zomato-gray">Loading dashboard...</div>
        </div>
      </div>
    )
  }

  if (error) {
    console.error('Dashboard error:', error)
    return (
      <div className="flex items-center justify-center min-h-screen bg-zomato-lightGray">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load dashboard</p>
          <p className="text-zomato-gray text-sm mb-4">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          {error && typeof error === 'object' && 'response' in error && (
            <p className="text-xs text-zomato-gray">
              {JSON.stringify((error as any).response?.data || {})}
            </p>
          )}
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zomato-lightGray">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">No dashboard data available</p>
        </div>
      </div>
    )
  }

  const onlineStatus = metrics?.restaurant?.is_online ?? false

  return (
    <div className="min-h-screen bg-zomato-lightGray">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-zomato-dark">{metrics?.restaurant?.name || 'Restaurant Dashboard'}</h1>
              <p className="text-sm text-zomato-gray mt-1">{metrics?.restaurant?.city || 'City'}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${onlineStatus ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <span className="text-sm font-medium text-zomato-dark">
                  {onlineStatus ? 'Online' : 'Offline'}
                </span>
              </div>
              <Button
                onClick={() => toggleOnlineMutation.mutate(!onlineStatus)}
                disabled={toggleOnlineMutation.isPending}
                className={`${onlineStatus ? 'bg-green-600 hover:bg-green-700' : 'bg-zomato-red hover:bg-zomato-darkRed'} text-white`}
              >
                {toggleOnlineMutation.isPending 
                  ? 'Updating...' 
                  : (onlineStatus ? 'Go Offline' : 'Go Online')}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white border-l-4 border-l-zomato-red">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zomato-gray">Today's Orders</CardTitle>
              <Package className="h-4 w-4 text-zomato-red" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-zomato-dark">{metrics?.orders?.today || 0}</div>
              <p className="text-xs text-zomato-gray mt-1">
                {metrics?.orders?.ongoing || 0} ongoing
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-green-500">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zomato-gray">Sales Today</CardTitle>
              <DollarSign className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-zomato-dark">
                {formatCurrency(metrics?.sales?.sales_today || 0)}
              </div>
              <p className="text-xs text-zomato-gray mt-1">
                Avg: {formatCurrency(metrics?.sales?.avg_order_value || 0)}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zomato-gray">Rating</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-zomato-dark">
                {metrics?.ratings?.current_rating 
                  ? Number(metrics.ratings.current_rating).toFixed(1) 
                  : '0.0'}
              </div>
              <p className="text-xs text-zomato-gray mt-1">
                {metrics?.ratings?.total_reviews || 0} reviews
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zomato-gray">Low Stock</CardTitle>
              <AlertCircle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-zomato-dark">
                {metrics?.inventory?.low_stock_items || 0}
              </div>
              <p className="text-xs text-zomato-gray mt-1">items need restocking</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Latest Orders */}
          <div className="lg:col-span-2">
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-zomato-dark">Latest Orders</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {metrics?.orders?.latest?.length ? (
                    metrics.orders.latest.map((order: any) => (
                      <div
                        key={order.id}
                        className="flex items-center justify-between p-3 bg-zomato-lightGray rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-zomato-dark">#{order.order_number}</span>
                            <span
                              className={`px-2 py-1 text-xs rounded-full ${
                                order.status === 'PENDING'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : order.status === 'PREPARING'
                                  ? 'bg-blue-100 text-blue-800'
                                  : order.status === 'READY'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {order.status}
                            </span>
                          </div>
                          <p className="text-sm text-zomato-gray mt-1">
                            {formatCurrency(order.total_amount)} • {order.items?.length || order.order_items?.length || 0} items
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-zomato-gray">
                            {order.created_at 
                              ? new Date(order.created_at).toLocaleTimeString('en-IN', {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : 'N/A'}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-zomato-gray">No recent orders</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Alerts */}
          <div>
            <Card className="bg-white">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold text-zomato-dark">Alerts</CardTitle>
                  {metrics?.alerts?.unread ? (
                    <span className="bg-zomato-red text-white text-xs font-semibold px-2 py-1 rounded-full">
                      {metrics.alerts.unread}
                    </span>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {metrics?.alerts?.latest?.length ? (
                    metrics.alerts.latest.map((alert: any) => (
                      <div
                        key={alert.id}
                        className={`p-3 rounded-lg border-l-4 ${
                          alert.severity === 'CRITICAL'
                            ? 'bg-red-50 border-red-500'
                            : alert.severity === 'WARNING'
                            ? 'bg-yellow-50 border-yellow-500'
                            : 'bg-blue-50 border-blue-500'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          {alert.severity === 'CRITICAL' ? (
                            <XCircle className="h-4 w-4 text-red-500 mt-0.5" />
                          ) : alert.severity === 'WARNING' ? (
                            <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5" />
                          ) : (
                            <CheckCircle2 className="h-4 w-4 text-blue-500 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className="text-sm font-medium text-zomato-dark">{alert.title}</p>
                            <p className="text-xs text-zomato-gray mt-1">{alert.message}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-zomato-gray">No alerts</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
