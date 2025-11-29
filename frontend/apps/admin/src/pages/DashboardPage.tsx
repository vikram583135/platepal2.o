import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { RefreshCw } from 'lucide-react'

export default function DashboardPage() {
  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/analytics/dashboard/')
      return response.data
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-500 mt-4">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    const errorMessage = (error as any)?.response?.data?.error ||
      (error as any)?.response?.data?.detail ||
      (error as any)?.message ||
      'An error occurred'

    const isRateLimit = errorMessage.toLowerCase().includes('rate limit') ||
      errorMessage.toLowerCase().includes('throttle')

    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-lg mb-2">Error loading dashboard</p>
              <p className="text-sm mb-4">{errorMessage}</p>
              {isRateLimit && (
                <p className="text-sm text-red-600 mb-4">
                  Too many requests. Please wait a moment before trying again.
                </p>
              )}
            </div>
            <Button
              onClick={() => refetch()}
              variant="outline"
              size="sm"
              className="ml-4 flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <Button
          onClick={() => refetch()}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="admin-card">
          <CardHeader>
            <CardTitle>Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.orders?.total || 0}</p>
          </CardContent>
        </Card>
        <Card className="admin-card">
          <CardHeader>
            <CardTitle>Today's Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">₹{analytics?.revenue?.today || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Restaurants</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.restaurants?.total || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Active Restaurants</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.restaurants?.active || 0}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

