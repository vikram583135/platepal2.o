import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { FileText, Upload, Check, X } from 'lucide-react'

interface Chargeback {
  id: number
  chargeback_id: string
  order: { order_number: string }
  amount: string
  reason: string
  status: string
  received_date: string
  due_date: string
  evidence_bundle: string[]
}

export default function ChargebacksPage() {
  const queryClient = useQueryClient()
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    chargeback?: Chargeback
    action?: string
  }>({ isOpen: false })

  const { data: chargebacks, isLoading } = useQuery({
    queryKey: ['chargebacks'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/chargebacks/')
      return response.data.results || response.data
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: async ({ chargebackId, status, notes }: { chargebackId: number; status: string; notes?: string }) => {
      return apiClient.post(`/admin/chargebacks/${chargebackId}/update_status/`, { status, notes })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chargebacks'] })
      setConfirmModal({ isOpen: false })
    },
  })

  const handleStatusChange = (chargeback: Chargeback, newStatus: string) => {
    setConfirmModal({ isOpen: true, chargeback, action: 'update_status' })
  }

  const handleConfirm = (notes?: string) => {
    const { chargeback, action } = confirmModal
    if (chargeback && action === 'update_status') {
      const newStatus = confirmModal.action === 'update_status' ? 'WON' : chargeback.status
      updateStatusMutation.mutate({
        chargebackId: chargeback.id,
        status: newStatus,
        notes
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'WON':
        return 'bg-green-100 text-green-800'
      case 'LOST':
        return 'bg-red-100 text-red-800'
      case 'EVIDENCE_SUBMITTED':
        return 'bg-blue-100 text-blue-800'
      case 'UNDER_REVIEW':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns: Column<Chargeback>[] = [
    {
      key: 'chargeback_id',
      header: 'Chargeback ID',
      accessor: (row) => (
        <code className="text-sm">{row.chargeback_id}</code>
      ),
      sortable: true,
    },
    {
      key: 'order',
      header: 'Order',
      accessor: (row) => row.order?.order_number || 'N/A',
    },
    {
      key: 'amount',
      header: 'Amount',
      accessor: (row) => `$${parseFloat(row.amount).toFixed(2)}`,
      sortable: true,
    },
    {
      key: 'reason',
      header: 'Reason',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.reason}>
          {row.reason}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(row.status)}`}>
          {row.status.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'due_date',
      header: 'Due Date',
      accessor: (row) => new Date(row.due_date).toLocaleDateString(),
      sortable: true,
    },
    {
      key: 'evidence',
      header: 'Evidence',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <span className="text-sm">{row.evidence_bundle?.length || 0} files</span>
          {row.evidence_bundle?.length === 0 && (
            <span className="text-xs text-red-600">No evidence</span>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Chargebacks</h1>
        <p className="text-gray-600">Manage chargeback disputes</p>
      </div>

      <DataTable
        data={chargebacks || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false })}
        onConfirm={handleConfirm}
        title="Update Chargeback Status"
        message="Are you sure you want to update the chargeback status?"
        confirmText="Update"
        requireReason
        variant="warning"
      />
    </div>
  )
}

