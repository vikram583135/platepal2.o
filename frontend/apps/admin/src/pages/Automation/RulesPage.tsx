import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { Plus, Play, Power, PowerOff } from 'lucide-react'

interface AutomationRule {
  id: number
  name: string
  description: string
  trigger_type: string
  action_type: string
  is_active: boolean
  priority: number
  created_at: string
}

export default function RulesPage() {
  const queryClient = useQueryClient()

  const { data: rules, isLoading } = useQuery({
    queryKey: ['automation-rules'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/automation/rules/')
      return response.data.results || response.data
    },
  })

  const toggleMutation = useMutation({
    mutationFn: async ({ ruleId, enable }: { ruleId: number; enable: boolean }) => {
      const endpoint = enable ? 'enable' : 'disable'
      return apiClient.post(`/admin/automation/rules/${ruleId}/${endpoint}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: async (ruleId: number) => {
      return apiClient.post(`/admin/automation/rules/${ruleId}/test/`)
    },
  })

  const columns: Column<AutomationRule>[] = [
    {
      key: 'name',
      header: 'Rule Name',
      accessor: (row) => row.name,
      sortable: true,
    },
    {
      key: 'description',
      header: 'Description',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.description}>
          {row.description || '-'}
        </div>
      ),
    },
    {
      key: 'trigger',
      header: 'Trigger',
      accessor: (row) => (
        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
          {row.trigger_type}
        </span>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      accessor: (row) => (
        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
          {row.action_type}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'priority',
      header: 'Priority',
      accessor: (row) => row.priority,
      sortable: true,
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => toggleMutation.mutate({ ruleId: row.id, enable: !row.is_active })}
            className="p-1 hover:bg-gray-100 rounded"
            title={row.is_active ? 'Disable' : 'Enable'}
          >
            {row.is_active ? (
              <PowerOff className="w-4 h-4 text-gray-600" />
            ) : (
              <Power className="w-4 h-4 text-green-600" />
            )}
          </button>
          <button
            onClick={() => testMutation.mutate(row.id)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Test Rule"
          >
            <Play className="w-4 h-4 text-blue-600" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Automation Rules</h1>
          <p className="text-gray-600">Create and manage automation rules</p>
        </div>
        <button
          onClick={() => {/* Show create modal */}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Rule
        </button>
      </div>

      <DataTable
        data={rules || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

