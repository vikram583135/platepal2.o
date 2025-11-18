import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Button } from '@/packages/ui/components/button'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { RefreshCw } from 'lucide-react'
import { formatCurrency, formatDate } from '@/packages/utils/format'

const statusColors: Record<string, 'default' | 'secondary' | 'destructive'> = {
  PENDING: 'secondary',
  ACCEPTED: 'default',
  PREPARING: 'default',
  READY: 'default',
  DELIVERED: 'default',
  CANCELLED: 'destructive',
}

export default function OrdersPage() {
  const navigate = useNavigate()
  
  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders'],
    queryFn: async () => {
      const response = await apiClient.get('/orders/orders/')
      return response.data.results || response.data
    },
  })

  const repeatOrderMutation = useMutation({
    mutationFn: async (orderId: number) => {
      const response = await apiClient.post(`/orders/orders/${orderId}/repeat/`)
      return response.data
    },
    onSuccess: (data) => {
      navigate(`/orders/${data.id}`)
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-32 w-full mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">My Orders</h1>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load orders. Please try again later.
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">My Orders</h1>

      {orders && orders.length > 0 ? (
        <div className="space-y-4">
          {orders.map((order: any) => (
            <Card key={order.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <Link to={`/orders/${order.id}`} className="flex-1">
                    <div>
                      <h3 className="text-lg font-semibold mb-1">
                        {order.restaurant?.name || 'Restaurant'}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Order #{order.order_number}
                      </p>
                    </div>
                  </Link>
                  <Badge variant={statusColors[order.status] || 'default'}>
                    {order.status}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <Link to={`/orders/${order.id}`} className="flex-1">
                    <div>
                      <p className="text-sm text-gray-600">
                        {formatDate(order.created_at)}
                      </p>
                      <p className="text-sm text-gray-600">
                        {order.items?.length || 0} item(s)
                      </p>
                    </div>
                  </Link>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <p className="font-semibold">{formatCurrency(order.total_amount, 'INR')}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault()
                          repeatOrderMutation.mutate(order.id)
                        }}
                        disabled={repeatOrderMutation.isPending}
                      >
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No orders yet</p>
          <Link to="/restaurants">
            <Button>Browse Restaurants</Button>
          </Link>
        </div>
      )}
    </div>
  )
}

