import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { BarChart3, TrendingUp, DollarSign, Users, AlertCircle } from 'lucide-react'
import { useRestaurantStore } from '../stores/restaurantStore'

export default function AnalyticsPage() {
  const { selectedRestaurantId } = useRestaurantStore()

  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['restaurant-dashboard', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/restaurants/dashboard/overview/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
  })

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view analytics</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-zomato-gray">Loading analytics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load analytics</p>
          <p className="text-zomato-gray text-sm">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen page-background p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zomato-dark">Analytics & Reports</h1>
        <p className="text-zomato-gray mt-1">Track your restaurant performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zomato-gray">Total Sales</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zomato-dark">
              ₹{dashboard?.sales?.sales_today?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-zomato-gray mt-1">Today</p>
          </CardContent>
        </Card>

        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zomato-gray">Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zomato-dark">{dashboard?.orders?.today || 0}</div>
            <p className="text-xs text-zomato-gray mt-1">Today</p>
          </CardContent>
        </Card>

        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zomato-gray">Average Order Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zomato-dark">
              ₹{dashboard?.sales?.avg_order_value?.toFixed(0) || '0'}
            </div>
            <p className="text-xs text-zomato-gray mt-1">Per order</p>
          </CardContent>
        </Card>

        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zomato-gray">Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zomato-dark">
              {dashboard?.ratings?.current_rating?.toFixed(1) || '0.0'}
            </div>
            <p className="text-xs text-zomato-gray mt-1">{dashboard?.ratings?.total_reviews || 0} reviews</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-zomato-dark">Analytics Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-16 text-zomato-gray">
            <BarChart3 className="h-16 w-16 mx-auto mb-4 text-zomato-gray opacity-50" />
            <p className="text-lg">Detailed analytics coming soon</p>
            <p className="text-sm mt-2">Sales reports, customer insights, and operational metrics will be available here</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
