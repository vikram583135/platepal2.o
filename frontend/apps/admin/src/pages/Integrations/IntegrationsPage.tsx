import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { CheckCircle, XCircle, Settings, Play } from 'lucide-react'

interface Integration {
  id: string
  name: string
  type: string
  status: string
  config: Record<string, any>
}

export default function IntegrationsPage() {
  const { data: integrations } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/integrations/')
      return response.data
    },
  })

  const { data: paymentGateways } = useQuery({
    queryKey: ['payment-gateways'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/integrations/payment_gateways/')
      return response.data
    },
  })

  const testMutation = useMutation({
    mutationFn: async (integrationId: string) => {
      return apiClient.post('/admin/integrations/test/', { integration_id: integrationId })
    },
    onSuccess: (data) => {
      alert(data.data?.message || 'Integration test completed')
    },
  })

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'payment_gateway':
        return 'bg-blue-100 text-blue-800'
      case 'sms':
        return 'bg-green-100 text-green-800'
      case 'email':
        return 'bg-purple-100 text-purple-800'
      case 'mapping':
        return 'bg-yellow-100 text-yellow-800'
      case 'accounting':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600">Manage external service integrations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations?.map((integration: Integration) => (
          <Card key={integration.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{integration.name}</CardTitle>
                {integration.status === 'active' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-gray-400" />
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(integration.type)}`}>
                  {integration.type.replace('_', ' ')}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {/* Show config modal */}}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  <Settings className="w-4 h-4" />
                  Configure
                </button>
                <button
                  onClick={() => testMutation.mutate(integration.id)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  <Play className="w-4 h-4" />
                  Test
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {paymentGateways && paymentGateways.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Payment Gateway Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {paymentGateways.map((gateway: any) => (
                <div key={gateway.name} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{gateway.name}</div>
                    <div className="text-sm text-gray-600">
                      {gateway.transactions_today} transactions today • {gateway.success_rate}% success rate
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      gateway.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {gateway.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

