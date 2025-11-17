import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Download, Trash2, Eye } from 'lucide-react'

export default function GDPRPage() {
  const [userId, setUserId] = useState('')
  const [exportData, setExportData] = useState<any>(null)
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; action: string }>({
    isOpen: false,
    action: ''
  })

  const exportMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason?: string }) => {
      const response = await apiClient.post('/admin/security/gdpr/export_user_data/', {
        user_id: userId,
        reason
      })
      return response.data
    },
    onSuccess: (data) => {
      setExportData(data)
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason?: string }) => {
      return apiClient.post('/admin/security/gdpr/delete_user_data/', {
        user_id: userId,
        reason
      })
    },
    onSuccess: () => {
      setConfirmModal({ isOpen: false, action: '' })
      setUserId('')
      alert('User data deleted successfully')
    },
  })

  const handleExport = () => {
    if (!userId) {
      alert('Please enter a user ID')
      return
    }
    setConfirmModal({ isOpen: true, action: 'export' })
  }

  const handleDelete = () => {
    if (!userId) {
      alert('Please enter a user ID')
      return
    }
    setConfirmModal({ isOpen: true, action: 'delete' })
  }

  const handleConfirm = (reason?: string) => {
    const id = parseInt(userId)
    if (isNaN(id)) {
      alert('Invalid user ID')
      return
    }

    if (confirmModal.action === 'export') {
      exportMutation.mutate({ userId: id, reason })
    } else if (confirmModal.action === 'delete') {
      deleteMutation.mutate({ userId: id, reason })
    }
  }

  const downloadExport = () => {
    if (!exportData) return
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `user-data-export-${userId}-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">GDPR Compliance</h1>
        <p className="text-gray-600">Manage user data exports and deletions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Data Export & Deletion</CardTitle>
          <CardDescription>Export or delete user data per GDPR requirements</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User ID
            </label>
            <input
              type="number"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Enter user ID"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleExport}
              disabled={!userId || exportMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              Export Data
            </button>
            <button
              onClick={handleDelete}
              disabled={!userId || deleteMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              Delete Data
            </button>
          </div>
        </CardContent>
      </Card>

      {exportData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Exported Data</CardTitle>
              <button
                onClick={downloadExport}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Download className="w-4 h-4" />
                Download JSON
              </button>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-50 p-4 rounded text-xs overflow-auto max-h-96">
              {JSON.stringify(exportData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: '' })}
        onConfirm={handleConfirm}
        title={confirmModal.action === 'export' ? 'Export User Data' : 'Delete User Data'}
        message={
          confirmModal.action === 'export'
            ? `Are you sure you want to export all data for user ${userId}?`
            : `Are you sure you want to permanently delete all data for user ${userId}? This action cannot be undone.`
        }
        confirmText={confirmModal.action === 'export' ? 'Export' : 'Delete'}
        requireReason
        variant={confirmModal.action === 'delete' ? 'danger' : 'warning'}
      />
    </div>
  )
}

