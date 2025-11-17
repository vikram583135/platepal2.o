import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ResponsiveContainer, AreaChart, Area, Tooltip, XAxis, YAxis, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import apiClient from '@/packages/api/client'
import { useRestaurantStore } from '../stores/restaurantStore'
import { Download, Calendar, TrendingUp, TrendingDown, DollarSign, CreditCard, AlertCircle, CheckCircle2, Clock } from 'lucide-react'
import { cn } from '@/packages/utils/cn'

interface FeedOrder {
  id: number
  total_amount: string
  created_at: string
}

export default function FinancePage() {
  const { selectedRestaurantId } = useRestaurantStore()
  const [dateRange, setDateRange] = useState<'today' | 'week' | 'month' | 'all'>('month')
  const [activeTab, setActiveTab] = useState<'overview' | 'settlements' | 'payouts' | 'refunds'>('overview')

  const ordersQuery = useQuery({
    queryKey: ['finance-orders', selectedRestaurantId, dateRange],
    queryFn: async () => {
      const params: any = { restaurant_id: selectedRestaurantId }
      const now = new Date()
      if (dateRange === 'today') {
        params.created_at__date = now.toISOString().split('T')[0]
      } else if (dateRange === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        params.created_at__gte = weekAgo.toISOString()
      } else if (dateRange === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        params.created_at__gte = monthAgo.toISOString()
      }
      const response = await apiClient.get('/orders/orders/', { params })
      return response.data.results || response.data
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const settlementsQuery = useQuery({
    queryKey: ['settlements', selectedRestaurantId],
    queryFn: async () => {
      const response = await apiClient.get('/payments/settlements/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data.results || response.data || []
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const payoutsQuery = useQuery({
    queryKey: ['payouts', selectedRestaurantId],
    queryFn: async () => {
      const response = await apiClient.get('/payments/payouts/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data.results || response.data || []
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const feedQuery = useQuery<{ latest_orders: FeedOrder[]; metrics?: { completed_today: number } }>({
    queryKey: ['finance-feed', selectedRestaurantId],
    queryFn: async () => {
      const response = await apiClient.get('/orders/orders/realtime_feed/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchInterval: 60000,
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  const stats = useMemo(() => {
    const delivered = (ordersQuery.data || []).filter((order: any) => order.status === 'DELIVERED')
    const cancelled = (ordersQuery.data || []).filter((order: any) => order.status === 'CANCELLED')
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const todayOrders = delivered.filter((order: any) => {
      const orderDate = new Date(order.delivered_at || order.created_at)
      orderDate.setHours(0, 0, 0, 0)
      return orderDate.getTime() === today.getTime()
    })
    const totalSales = delivered.reduce((sum: number, order: any) => sum + Number(order.total_amount || 0), 0)
    const todaysSales = todayOrders.reduce((sum: number, order: any) => sum + Number(order.total_amount || 0), 0)
    const avgOrder = delivered.length ? totalSales / delivered.length : 0
    const totalRefunds = cancelled.reduce((sum: number, order: any) => sum + Number(order.total_amount || 0), 0)
    const commission = totalSales * 0.15 // 15% commission
    const netPayout = totalSales - commission
    
    return { 
      totalSales, 
      todaysSales, 
      avgOrder, 
      deliveredCount: delivered.length,
      totalRefunds,
      commission,
      netPayout,
    }
  }, [ordersQuery.data])

  const chartData = useMemo(() => {
    const grouped: Record<string, number> = {}
    feedQuery.data?.latest_orders?.forEach((order) => {
      const day = new Date(order.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
      grouped[day] = (grouped[day] || 0) + Number(order.total_amount)
    })
    return Object.entries(grouped).map(([day, amount]) => ({ day, amount }))
  }, [feedQuery.data])

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view finance</p>
        </div>
      </div>
    )
  }

  if (ordersQuery.isLoading || feedQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading finance data...</p>
      </div>
    )
  }

  if (ordersQuery.error || feedQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load finance data</p>
          <p className="text-zomato-gray text-sm">
            {(ordersQuery.error || feedQuery.error) instanceof Error 
              ? (ordersQuery.error || feedQuery.error)?.message 
              : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

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

  const formatDate = (dateString: string | undefined | null) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-IN', { 
        day: 'numeric', 
        month: 'short', 
        year: 'numeric' 
      })
    } catch {
      return 'N/A'
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      COMPLETED: 'bg-green-100 text-green-700',
      PROCESSING: 'bg-blue-100 text-blue-700',
      PENDING: 'bg-yellow-100 text-yellow-700',
      FAILED: 'bg-red-100 text-red-700',
      INITIATED: 'bg-purple-100 text-purple-700',
    }
    return colors[status] || 'bg-gray-100 text-gray-700'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'COMPLETED') return <CheckCircle2 className="h-4 w-4" />
    if (status === 'PROCESSING' || status === 'INITIATED') return <Clock className="h-4 w-4" />
    if (status === 'FAILED') return <AlertCircle className="h-4 w-4" />
    return <Clock className="h-4 w-4" />
  }

  return (
    <div className="min-h-screen bg-zomato-lightGray p-6">
      <div className="space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-zomato-dark">Finance & Settlements</h1>
            <p className="text-sm text-zomato-gray mt-1">Track payouts, commissions, and refunds in real time.</p>
          </div>
          <div className="flex gap-2">
            {(['today', 'week', 'month', 'all'] as const).map((range) => (
              <Button
                key={range}
                size="sm"
                variant={dateRange === range ? 'default' : 'outline'}
                onClick={() => setDateRange(range)}
                className={dateRange === range ? 'bg-zomato-red hover:bg-zomato-darkRed text-white' : ''}
              >
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </Button>
            ))}
          </div>
        </header>

        <div className="flex gap-2 border-b">
          {(['overview', 'settlements', 'payouts', 'refunds'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab
                  ? 'border-zomato-red text-zomato-red'
                  : 'border-transparent text-zomato-gray hover:text-zomato-dark'
              )}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card className="bg-white shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zomato-gray">Total Sales</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-zomato-dark">{formatCurrency(stats.totalSales)}</p>
                  <p className="text-xs text-zomato-gray mt-1">{stats.deliveredCount} delivered orders</p>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zomato-gray">Net Payout</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(stats.netPayout)}</p>
                  <p className="text-xs text-zomato-gray mt-1">After commission</p>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zomato-gray">Commission</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-orange-600">{formatCurrency(stats.commission)}</p>
                  <p className="text-xs text-zomato-gray mt-1">15% of sales</p>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zomato-gray">Avg Order Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-zomato-dark">{formatCurrency(stats.avgOrder)}</p>
                  <p className="text-xs text-zomato-gray mt-1">Per order</p>
                </CardContent>
              </Card>
            </div>

        <Card className="bg-white shadow-md">
          <CardHeader>
            <CardTitle className="text-zomato-dark">Revenue Trend</CardTitle>
            <CardDescription className="text-zomato-gray">Based on recent orders.</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E23744" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#E23744" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#8E8E8E" />
                <YAxis stroke="#8E8E8E" />
                <Tooltip />
                <Area type="monotone" dataKey="amount" stroke="#E23744" fillOpacity={1} fill="url(#colorSales)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-white shadow-md">
                <CardHeader>
                  <CardTitle className="text-zomato-dark">Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-zomato-gray">Gross Sales</span>
                      <span className="font-semibold text-zomato-dark">{formatCurrency(stats.totalSales)}</span>
                    </div>
                    <div className="flex items-center justify-between text-red-600">
                      <span>Commission (15%)</span>
                      <span className="font-semibold">-{formatCurrency(stats.commission)}</span>
                    </div>
                    <div className="border-t pt-2 flex items-center justify-between">
                      <span className="font-semibold text-zomato-dark">Net Payout</span>
                      <span className="font-bold text-green-600 text-lg">{formatCurrency(stats.netPayout)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-md">
                <CardHeader>
                  <CardTitle className="text-zomato-dark">Refunds</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(stats.totalRefunds)}</p>
                  <p className="text-xs text-zomato-gray mt-1">Total refunded amount</p>
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {activeTab === 'settlements' && (
          <div className="space-y-4">
            {settlementsQuery.data?.length > 0 ? (
              settlementsQuery.data.map((settlement: any) => (
                <Card key={settlement.id} className="bg-white shadow-md">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-zomato-dark">
                          Settlement Cycle: {formatDate(settlement.cycle_start)} - {formatDate(settlement.cycle_end)}
                        </CardTitle>
                        <CardDescription className="text-zomato-gray mt-1">
                          {settlement.payout_reference && `Reference: ${settlement.payout_reference}`}
                        </CardDescription>
                      </div>
                      <span className={cn('px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1', getStatusColor(settlement.status))}>
                        {getStatusIcon(settlement.status)}
                        {settlement.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-zomato-gray text-xs">Total Sales</p>
                        <p className="font-semibold text-zomato-dark">{formatCurrency(Number(settlement.total_sales))}</p>
                      </div>
                      <div>
                        <p className="text-zomato-gray text-xs">Commission</p>
                        <p className="font-semibold text-red-600">-{formatCurrency(Number(settlement.commission_amount))}</p>
                      </div>
                      <div>
                        <p className="text-zomato-gray text-xs">Fees</p>
                        <p className="font-semibold text-orange-600">-{formatCurrency(Number(settlement.packaging_fee) + Number(settlement.delivery_fee_share))}</p>
                      </div>
                      <div>
                        <p className="text-zomato-gray text-xs">Net Payout</p>
                        <p className="font-bold text-green-600 text-lg">{formatCurrency(Number(settlement.net_payout))}</p>
                      </div>
                    </div>
                    {settlement.processed_at && (
                      <p className="text-xs text-zomato-gray mt-4">
                        Processed: {formatDate(settlement.processed_at)}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card className="bg-white shadow-md">
                <CardContent className="py-12 text-center">
                  <p className="text-zomato-gray">No settlements found</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'payouts' && (
          <div className="space-y-4">
            {payoutsQuery.data?.length > 0 ? (
              payoutsQuery.data.map((payout: any) => (
                <Card key={payout.id} className="bg-white shadow-md">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-zomato-dark">{formatCurrency(Number(payout.amount))}</CardTitle>
                        <CardDescription className="text-zomato-gray mt-1">
                          {payout.bank_name && `${payout.bank_name} • ${payout.account_holder_name}`}
                          {payout.utr_number && ` • UTR: ${payout.utr_number}`}
                        </CardDescription>
                      </div>
                      <span className={cn('px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1', getStatusColor(payout.status))}>
                        {getStatusIcon(payout.status)}
                        {payout.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zomato-gray">
                        {payout.initiated_at ? `Initiated: ${formatDate(payout.initiated_at)}` : 'Pending initiation'}
                      </span>
                      {payout.processed_at && (
                        <span className="text-zomato-gray">
                          Processed: {formatDate(payout.processed_at)}
                        </span>
                      )}
                    </div>
                    {payout.failure_reason && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                        <strong>Failure Reason:</strong> {payout.failure_reason}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card className="bg-white shadow-md">
                <CardContent className="py-12 text-center">
                  <p className="text-zomato-gray">No payouts found</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'refunds' && (
          <Card className="bg-white shadow-md">
            <CardHeader>
              <CardTitle className="text-zomato-dark">Refund History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(ordersQuery.data || [])
                  .filter((order: any) => order.status === 'CANCELLED' && Number(order.total_amount) > 0)
                  .map((order: any) => (
                    <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <p className="font-semibold text-zomato-dark">Order #{order.order_number}</p>
                        <p className="text-xs text-zomato-gray">{formatDate(order.cancelled_at || order.created_at)}</p>
                        {order.cancellation_reason && (
                          <p className="text-xs text-zomato-gray mt-1">{order.cancellation_reason}</p>
                        )}
                      </div>
                      <p className="font-semibold text-red-600">{formatCurrency(Number(order.total_amount))}</p>
                    </div>
                  ))}
                {!ordersQuery.data?.some((order: any) => order.status === 'CANCELLED' && Number(order.total_amount) > 0) && (
                  <p className="text-center py-8 text-zomato-gray">No refunds found</p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'overview' && (
          <Card className="bg-white shadow-md">
            <CardHeader>
              <CardTitle className="text-zomato-dark">Revenue Trend</CardTitle>
              <CardDescription className="text-zomato-gray">Based on recent orders.</CardDescription>
            </CardHeader>
            <CardContent className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#E23744" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#E23744" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" stroke="#8E8E8E" />
                  <YAxis stroke="#8E8E8E" />
                  <Tooltip />
                  <Area type="monotone" dataKey="amount" stroke="#E23744" fillOpacity={1} fill="url(#colorSales)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
