import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function ExecutiveDashboardPage() {
  const { data: analytics } = useQuery({
    queryKey: ['executive-analytics'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/analytics/dashboard/')
      return response.data
    },
  })

  // Mock chart data - in production, this would come from the API
  const revenueData = [
    { date: 'Mon', revenue: 4500 },
    { date: 'Tue', revenue: 5200 },
    { date: 'Wed', revenue: 4800 },
    { date: 'Thu', revenue: 6100 },
    { date: 'Fri', revenue: 5500 },
    { date: 'Sat', revenue: 7200 },
    { date: 'Sun', revenue: 6800 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
        <p className="text-gray-600">Key metrics and performance indicators</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">Total GMV</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">${analytics?.revenue?.week?.toLocaleString() || '0'}</p>
            <p className="text-sm text-gray-500 mt-1">This week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">Orders Today</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.orders?.today || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Total: {analytics?.orders?.total || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">Active Restaurants</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.restaurants?.active || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Total: {analytics?.restaurants?.total || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-600">AOV</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">$24.50</p>
            <p className="text-sm text-gray-500 mt-1">Average order value</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend (Last 7 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

