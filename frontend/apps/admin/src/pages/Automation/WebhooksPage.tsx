import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { Plus, Play, Eye, AlertCircle } from 'lucide-react'

interface Webhook {
  id: number
  name: string
  url: string
  events: string[]
  status: string
  is_active: boolean
  last_triggered_at: string | null
  failure_count: number
}

export default function WebhooksPage() {
  const queryClient = useQueryClient()
  const [selectedWebhook, setSelectedWebhook] = useState<number | null>(null)

  const { data: webhooks, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/automation/webhooks/')
      return response.data.results || response.data
    },
  })

  const testMutation = useMutation({
    mutationFn: async (webhookId: number) => {
      return apiClient.post(`/admin/automation/webhooks/${webhookId}/test/`, {
        payload: { test: true }
      })
    },
    onSuccess: () => {
      alert('Test webhook sent')
    },
  })

  const retryMutation = useMutation({
    mutationFn: async (webhookId: number) => {
      return apiClient.post(`/admin/automation/webhooks/${webhookId}/retry_failed/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] })
      alert('Failed deliveries queued for retry')
    },
  })

  const columns: Column<Webhook>[] = [
    {
      key: 'name',
      header: 'Name',
      accessor: (row) => row.name,
      sortable: true,
    },
    {
      key: 'url',
      header: 'URL',
      accessor: (row) => (
        <code className="text-sm bg-gray-100 px-2 py-1 rounded">{row.url}</code>
      ),
    },
    {
      key: 'events',
      header: 'Events',
      accessor: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.events.slice(0, 2).map((event, i) => (
            <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
              {event}
            </span>
          ))}
          {row.events.length > 2 && (
            <span className="text-xs text-gray-500">+{row.events.length - 2}</span>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            row.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
            row.status === 'FAILING' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {row.status}
          </span>
          {row.failure_count > 0 && (
            <AlertCircle className="w-4 h-4 text-red-600" />
          )}
        </div>
      ),
    },
    {
      key: 'last_triggered',
      header: 'Last Triggered',
      accessor: (row) => row.last_triggered_at
        ? new Date(row.last_triggered_at).toLocaleDateString()
        : 'Never',
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => testMutation.mutate(row.id)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Test Webhook"
          >
            <Play className="w-4 h-4 text-blue-600" />
          </button>
          <button
            onClick={() => setSelectedWebhook(row.id)}
            className="p-1 hover:bg-gray-100 rounded"
            title="View Deliveries"
          >
            <Eye className="w-4 h-4 text-gray-600" />
          </button>
          {row.failure_count > 0 && (
            <button
              onClick={() => retryMutation.mutate(row.id)}
              className="p-1 hover:bg-gray-100 rounded text-orange-600"
              title="Retry Failed"
            >
              <AlertCircle className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
          <p className="text-gray-600">Manage webhook integrations</p>
        </div>
        <button
          onClick={() => {/* Show create modal */}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Webhook
        </button>
      </div>

      <DataTable
        data={webhooks || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

