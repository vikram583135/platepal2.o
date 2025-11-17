import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Plus, RotateCcw, ToggleLeft, ToggleRight } from 'lucide-react'

interface FeatureFlag {
  id: number
  name: string
  description: string
  is_enabled: boolean
  rollout_percentage: number
  target_audience: Record<string, any>
  created_at: string
}

export default function FeatureFlagsPage() {
  const queryClient = useQueryClient()
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    flag?: FeatureFlag
    action?: string
  }>({ isOpen: false })

  const { data: flags, isLoading } = useQuery({
    queryKey: ['feature-flags'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/feature-flags/')
      return response.data.results || response.data
    },
  })

  const toggleMutation = useMutation({
    mutationFn: async ({ flagId, enabled, percentage, reason }: { flagId: number; enabled: boolean; percentage: number; reason?: string }) => {
      return apiClient.patch(`/admin/feature-flags/${flagId}/`, {
        is_enabled: enabled,
        rollout_percentage: percentage,
        reason
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] })
      setConfirmModal({ isOpen: false })
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: async ({ flagId, reason }: { flagId: number; reason?: string }) => {
      return apiClient.post(`/admin/feature-flags/${flagId}/rollback/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] })
      setConfirmModal({ isOpen: false })
      alert('Feature flag rolled back')
    },
  })

  const handleToggle = (flag: FeatureFlag) => {
    setConfirmModal({ isOpen: true, flag, action: 'toggle' })
  }

  const handleRollback = (flag: FeatureFlag) => {
    setConfirmModal({ isOpen: true, flag, action: 'rollback' })
  }

  const handleConfirm = (reason?: string) => {
    const { flag, action } = confirmModal
    if (!flag) return

    if (action === 'toggle') {
      toggleMutation.mutate({
        flagId: flag.id,
        enabled: !flag.is_enabled,
        percentage: flag.is_enabled ? 0 : flag.rollout_percentage,
        reason
      })
    } else if (action === 'rollback') {
      rollbackMutation.mutate({ flagId: flag.id, reason })
    }
  }

  const columns: Column<FeatureFlag>[] = [
    {
      key: 'name',
      header: 'Flag Name',
      accessor: (row) => (
        <div>
          <div className="font-medium">{row.name}</div>
          {row.description && (
            <div className="text-sm text-gray-500">{row.description}</div>
          )}
        </div>
      ),
      sortable: true,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          {row.is_enabled ? (
            <ToggleRight className="w-5 h-5 text-green-600" />
          ) : (
            <ToggleLeft className="w-5 h-5 text-gray-400" />
          )}
          <span className={`px-2 py-1 text-xs rounded-full ${
            row.is_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {row.is_enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      ),
    },
    {
      key: 'rollout',
      header: 'Rollout',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <div className="w-32 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${row.rollout_percentage}%` }}
            />
          </div>
          <span className="text-sm font-medium">{row.rollout_percentage}%</span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => handleToggle(row)}
            className="p-1 hover:bg-gray-100 rounded"
            title={row.is_enabled ? 'Disable' : 'Enable'}
          >
            {row.is_enabled ? (
              <ToggleRight className="w-4 h-4 text-gray-600" />
            ) : (
              <ToggleLeft className="w-4 h-4 text-green-600" />
            )}
          </button>
          {row.is_enabled && (
            <button
              onClick={() => handleRollback(row)}
              className="p-1 hover:bg-gray-100 rounded"
              title="Rollback"
            >
              <RotateCcw className="w-4 h-4 text-red-600" />
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
          <h1 className="text-2xl font-bold text-gray-900">Feature Flags</h1>
          <p className="text-gray-600">Manage feature flags and gradual rollouts</p>
        </div>
        <button
          onClick={() => {/* Show create modal */}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Flag
        </button>
      </div>

      <DataTable
        data={flags || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false })}
        onConfirm={handleConfirm}
        title={
          confirmModal.action === 'rollback' ? 'Rollback Feature Flag' :
          confirmModal.flag?.is_enabled ? 'Disable Feature Flag' : 'Enable Feature Flag'
        }
        message={
          confirmModal.action === 'rollback'
            ? `Are you sure you want to rollback ${confirmModal.flag?.name}? This will disable it immediately.`
            : `Are you sure you want to ${confirmModal.flag?.is_enabled ? 'disable' : 'enable'} ${confirmModal.flag?.name}?`
        }
        confirmText={confirmModal.action === 'rollback' ? 'Rollback' : confirmModal.flag?.is_enabled ? 'Disable' : 'Enable'}
        requireReason
        variant={confirmModal.action === 'rollback' ? 'danger' : 'warning'}
      />
    </div>
  )
}

