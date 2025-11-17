import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Plus, Check, X, TrendingUp } from 'lucide-react'

interface Campaign {
  id: number
  name: string
  code: string
  restaurant: { name: string } | null
  offer_type: string
  discount_type: string
  discount_value: string
  is_active: boolean
  valid_from: string
  valid_until: string
  uses_count: number
  max_uses: number | null
}

export default function CampaignsPage() {
  const queryClient = useQueryClient()
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    action: string
    campaign?: Campaign
  }>({ isOpen: false, action: '' })

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['admin-campaigns'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/campaigns/')
      return response.data.results || response.data
    },
  })

  const approveMutation = useMutation({
    mutationFn: async ({ campaignId, reason }: { campaignId: number; reason?: string }) => {
      return apiClient.post(`/admin/campaigns/${campaignId}/approve/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-campaigns'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async ({ campaignId, reason }: { campaignId: number; reason?: string }) => {
      return apiClient.post(`/admin/campaigns/${campaignId}/reject/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-campaigns'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const handleAction = (campaign: Campaign, action: string) => {
    setConfirmModal({ isOpen: true, action, campaign })
  }

  const handleConfirm = (reason?: string) => {
    const { action, campaign } = confirmModal
    if (!campaign) return

    if (action === 'approve') {
      approveMutation.mutate({ campaignId: campaign.id, reason })
    } else if (action === 'reject') {
      rejectMutation.mutate({ campaignId: campaign.id, reason })
    }
  }

  const columns: Column<Campaign>[] = [
    {
      key: 'name',
      header: 'Campaign Name',
      accessor: (row) => row.name,
      sortable: true,
    },
    {
      key: 'code',
      header: 'Code',
      accessor: (row) => (
        <code className="px-2 py-1 bg-gray-100 rounded text-sm">{row.code || 'N/A'}</code>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.offer_type === 'PLATFORM' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
        }`}>
          {row.offer_type}
        </span>
      ),
    },
    {
      key: 'restaurant',
      header: 'Restaurant',
      accessor: (row) => row.restaurant?.name || 'Platform',
    },
    {
      key: 'discount',
      header: 'Discount',
      accessor: (row) => {
        if (row.discount_type === 'PERCENTAGE') {
          return `${row.discount_value}%`
        }
        return `$${row.discount_value}`
      },
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'usage',
      header: 'Usage',
      accessor: (row) => (
        <div className="text-sm">
          {row.uses_count} / {row.max_uses || '∞'}
        </div>
      ),
    },
    {
      key: 'validity',
      header: 'Valid Until',
      accessor: (row) => new Date(row.valid_until).toLocaleDateString(),
      sortable: true,
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (row) => (
        <div className="flex gap-2">
          {!row.is_active && (
            <button
              onClick={() => handleAction(row, 'approve')}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="Approve"
            >
              <Check className="w-4 h-4" />
            </button>
          )}
          {row.is_active && (
            <button
              onClick={() => handleAction(row, 'reject')}
              className="p-1 text-red-600 hover:bg-red-50 rounded"
              title="Reject"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => {/* Navigate to performance */}}
            className="p-1 text-blue-600 hover:bg-blue-50 rounded"
            title="View Performance"
          >
            <TrendingUp className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="text-gray-600">Manage platform and merchant campaigns</p>
        </div>
        <button
          onClick={() => {/* Show create modal */}}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Platform Campaign
        </button>
      </div>

      <DataTable
        data={campaigns || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: '' })}
        onConfirm={handleConfirm}
        title={confirmModal.action === 'approve' ? 'Approve Campaign' : 'Reject Campaign'}
        message={
          confirmModal.action === 'approve'
            ? `Are you sure you want to approve this campaign?`
            : `Are you sure you want to reject this campaign?`
        }
        confirmText={confirmModal.action === 'approve' ? 'Approve' : 'Reject'}
        requireReason
        variant={confirmModal.action === 'reject' ? 'danger' : 'warning'}
      />
    </div>
  )
}

