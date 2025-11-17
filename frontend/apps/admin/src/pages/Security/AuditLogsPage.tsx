import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'
import { AuditTimeline, AuditEvent } from '@/packages/ui/components/AuditTimeline'

interface AuditLog {
  id: number
  user_email: string
  action: string
  resource_type: string
  resource_id: string
  before_state: Record<string, any>
  after_state: Record<string, any>
  reason: string
  created_at: string
  ip_address: string
}

export default function AuditLogsPage() {
  const [filters, setFilters] = useState({
    user_id: '',
    resource_type: '',
    action: '',
    date_from: '',
    date_to: '',
  })

  const { data: auditLogs, isLoading } = useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: async () => {
      const params: any = {}
      if (filters.user_id) params.user_id = filters.user_id
      if (filters.resource_type) params.resource_type = filters.resource_type
      if (filters.action) params.action = filters.action
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
      
      const response = await apiClient.get('/admin/audit-logs/', { params })
      return response.data.results || response.data
    },
  })

  const columns: Column<AuditLog>[] = [
    {
      key: 'created_at',
      header: 'Timestamp',
      accessor: (row) => new Date(row.created_at).toLocaleString(),
      sortable: true,
    },
    {
      key: 'user',
      header: 'User',
      accessor: (row) => row.user_email || 'System',
      sortable: true,
    },
    {
      key: 'action',
      header: 'Action',
      accessor: (row) => (
        <code className="px-2 py-1 bg-gray-100 rounded text-sm">{row.action}</code>
      ),
      sortable: true,
    },
    {
      key: 'resource',
      header: 'Resource',
      accessor: (row) => (
        <div>
          <span className="font-medium">{row.resource_type}</span>
          <span className="text-gray-500 ml-2">#{row.resource_id}</span>
        </div>
      ),
    },
    {
      key: 'reason',
      header: 'Reason',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.reason}>
          {row.reason || '-'}
        </div>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP Address',
      accessor: (row) => row.ip_address || '-',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600">View all admin actions and changes</p>
        </div>
        <CSVExporter
          data={auditLogs || []}
          filename={`audit-logs-${new Date().toISOString().split('T')[0]}.csv`}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 bg-gray-50 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
          <input
            type="text"
            value={filters.user_id}
            onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="Filter by user"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Resource Type</label>
          <input
            type="text"
            value={filters.resource_type}
            onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="e.g., user, order"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
          <input
            type="text"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="e.g., user.ban"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
      </div>

      <DataTable
        data={auditLogs || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

