import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function HealthDashboardPage() {
  const { data: healthData } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/system/health/dashboard/')
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Activity className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'critical':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
        <p className="text-gray-600">Monitor system performance and health metrics</p>
      </div>

      {healthData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(healthData).map(([service, data]: [string, any]) => (
            <Card key={service}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{service}</CardTitle>
                  {getStatusIcon(data.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 ${getStatusColor(data.status)}`}>
                  {data.status.toUpperCase()}
                </div>
                <div className="space-y-2">
                  {Object.entries(data.metrics || {}).map(([metric, info]: [string, any]) => (
                    <div key={metric} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{metric}:</span>
                      <span className="font-medium">{info.current}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

