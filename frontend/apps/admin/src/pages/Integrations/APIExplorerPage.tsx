import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Play, Code } from 'lucide-react'

interface Endpoint {
  path: string
  method: string
  description: string
  permissions: string[]
}

export default function APIExplorerPage() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null)
  const [testPayload, setTestPayload] = useState('{}')
  const [testResponse, setTestResponse] = useState<any>(null)

  const { data: endpoints } = useQuery({
    queryKey: ['api-endpoints'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/api-explorer/endpoints/')
      return response.data
    },
  })

  const testMutation = useMutation({
    mutationFn: async ({ path, method, payload }: { path: string; method: string; payload: any }) => {
      return apiClient.post('/admin/api-explorer/test_endpoint/', {
        path,
        method,
        payload: JSON.parse(payload)
      })
    },
    onSuccess: (data) => {
      setTestResponse(data.data)
    },
  })

  const handleTest = () => {
    if (!selectedEndpoint) return
    testMutation.mutate({
      path: selectedEndpoint.path,
      method: selectedEndpoint.method,
      payload: testPayload
    })
  }

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET':
        return 'bg-blue-100 text-blue-800'
      case 'POST':
        return 'bg-green-100 text-green-800'
      case 'PUT':
        return 'bg-yellow-100 text-yellow-800'
      case 'DELETE':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">API Explorer</h1>
        <p className="text-gray-600">Explore and test admin API endpoints</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Available Endpoints</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {endpoints?.map((endpoint: Endpoint, index: number) => (
                <div
                  key={index}
                  onClick={() => setSelectedEndpoint(endpoint)}
                  className={`p-3 rounded cursor-pointer border ${
                    selectedEndpoint?.path === endpoint.path
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 text-xs rounded font-mono ${getMethodColor(endpoint.method)}`}>
                      {endpoint.method}
                    </span>
                    <code className="text-sm font-mono">{endpoint.path}</code>
                  </div>
                  <p className="text-sm text-gray-600">{endpoint.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {endpoint.permissions.map((perm, i) => (
                      <span key={i} className="px-2 py-1 text-xs bg-gray-100 rounded">
                        {perm}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Test Endpoint</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedEndpoint ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Endpoint
                  </label>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded ${getMethodColor(selectedEndpoint.method)}`}>
                      {selectedEndpoint.method}
                    </span>
                    <code className="text-sm font-mono flex-1 bg-gray-100 px-2 py-1 rounded">
                      {selectedEndpoint.path}
                    </code>
                  </div>
                </div>

                {selectedEndpoint.method !== 'GET' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Request Payload (JSON)
                    </label>
                    <textarea
                      value={testPayload}
                      onChange={(e) => setTestPayload(e.target.value)}
                      rows={6}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                      placeholder='{"key": "value"}'
                    />
                  </div>
                )}

                <button
                  onClick={handleTest}
                  disabled={testMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  {testMutation.isPending ? 'Testing...' : 'Test Endpoint'}
                </button>

                {testResponse && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Response
                    </label>
                    <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-64">
                      {JSON.stringify(testResponse, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-gray-500 py-8">
                Select an endpoint to test
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

