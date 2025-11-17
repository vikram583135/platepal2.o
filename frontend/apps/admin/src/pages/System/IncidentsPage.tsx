import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Plus, AlertTriangle } from 'lucide-react'

interface Incident {
  id: number
  title: string
  description: string
  status: string
  severity: string
  affected_services: string[]
  reported_by: { email: string } | null
  created_at: string
  resolved_at: string | null
}

export default function IncidentsPage() {
  const queryClient = useQueryClient()
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    incident?: Incident
    newStatus?: string
  }>({ isOpen: false })

  const { data: incidents, isLoading } = useQuery({
    queryKey: ['admin-incidents'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/system/incidents/')
      return response.data.results || response.data
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: async ({ incidentId, status, message }: { incidentId: number; status: string; message?: string }) => {
      return apiClient.post(`/admin/system/incidents/${incidentId}/update_status/`, { status, message })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-incidents'] })
      setConfirmModal({ isOpen: false })
    },
  })

  const handleStatusChange = (incident: Incident, newStatus: string) => {
    setConfirmModal({ isOpen: true, incident, newStatus })
  }

  const handleConfirm = (message?: string) => {
    const { incident, newStatus } = confirmModal
    if (incident && newStatus) {
      updateStatusMutation.mutate({
        incidentId: incident.id,
        status: newStatus,
        message
      })
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-blue-100 text-blue-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'bg-red-100 text-red-800'
      case 'INVESTIGATING':
        return 'bg-yellow-100 text-yellow-800'
      case 'RESOLVED':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns: Column<Incident>[] = [
    {
      key: 'title',
      header: 'Title',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <span className="font-medium">{row.title}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: 'severity',
      header: 'Severity',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(row.severity)}`}>
          {row.severity}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(row.status)}`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'services',
      header: 'Affected Services',
      accessor: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.affected_services?.slice(0, 2).map((service: string, i: number) => (
            <span key={i} className="px-2 py-1 text-xs bg-gray-100 rounded">
              {service}
            </span>
          ))}
          {row.affected_services?.length > 2 && (
            <span className="text-xs text-gray-500">+{row.affected_services.length - 2}</span>
          )}
        </div>
      ),
    },
    {
      key: 'reported_by',
      header: 'Reported By',
      accessor: (row) => row.reported_by?.email || 'System',
    },
    {
      key: 'created_at',
      header: 'Created',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
          <p className="text-gray-600">Manage system incidents and outages</p>
        </div>
        <button
          onClick={() => {/* Show create modal */}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Incident
        </button>
      </div>

      <DataTable
        data={incidents || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false })}
        onConfirm={handleConfirm}
        title="Update Incident Status"
        message={`Are you sure you want to change the status to ${confirmModal.newStatus}?`}
        confirmText="Update"
        requireReason
        variant="warning"
      />
    </div>
  )
}

