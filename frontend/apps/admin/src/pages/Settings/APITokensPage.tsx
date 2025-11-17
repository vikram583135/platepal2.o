import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Plus, Trash2, RotateCcw, Copy, Check } from 'lucide-react'

interface APIToken {
  id: number
  name: string
  token_display: string
  token_prefix: string
  scopes: string[]
  expires_at: string | null
  last_used_at: string | null
  is_active: boolean
  rate_limit: number
  created_at: string
}

export default function APITokensPage() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newToken, setNewToken] = useState({ name: '', scopes: [] as string[], expires_at: '' })
  const [copiedToken, setCopiedToken] = useState<number | null>(null)
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; action: string; token?: APIToken }>({
    isOpen: false,
    action: ''
  })

  const { data: tokens, isLoading } = useQuery({
    queryKey: ['api-tokens'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/api-tokens/')
      return response.data.results || response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post('/admin/api-tokens/', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
      setNewToken({ name: '', scopes: [], expires_at: '' })
      setShowCreateModal(false)
      // Show the token once
      alert(`Token created! Save it securely: ${data.token}`)
    },
  })

  const revokeMutation = useMutation({
    mutationFn: async ({ tokenId, reason }: { tokenId: number; reason?: string }) => {
      return apiClient.post(`/admin/api-tokens/${tokenId}/revoke/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const rotateMutation = useMutation({
    mutationFn: async ({ tokenId, reason }: { tokenId: number; reason?: string }) => {
      const response = await apiClient.post(`/admin/api-tokens/${tokenId}/rotate/`, { reason })
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
      setConfirmModal({ isOpen: false, action: '' })
      alert(`Token rotated! New token: ${data.token}`)
    },
  })

  const handleCopy = (token: string, id: number) => {
    navigator.clipboard.writeText(token)
    setCopiedToken(id)
    setTimeout(() => setCopiedToken(null), 2000)
  }

  const columns: Column<APIToken>[] = [
    {
      key: 'name',
      header: 'Name',
      accessor: (row) => row.name,
      sortable: true,
    },
    {
      key: 'token',
      header: 'Token',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">{row.token_display}</code>
          {row.token_display.includes('...') ? null : (
            <button
              onClick={() => handleCopy(row.token_display, row.id)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              {copiedToken === row.id ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      ),
    },
    {
      key: 'scopes',
      header: 'Scopes',
      accessor: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.scopes.map((scope, i) => (
            <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
              {scope}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {row.is_active ? 'Active' : 'Revoked'}
        </span>
      ),
    },
    {
      key: 'last_used',
      header: 'Last Used',
      accessor: (row) => row.last_used_at
        ? new Date(row.last_used_at).toLocaleDateString()
        : 'Never',
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Tokens</h1>
          <p className="text-gray-600">Manage API tokens for automation and scripts</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Create Token
        </button>
      </div>

      <DataTable
        data={tokens || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <Card className="max-w-md w-full mx-4">
            <CardHeader>
              <CardTitle>Create API Token</CardTitle>
              <CardDescription>Generate a new API token for automation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newToken.name}
                  onChange={(e) => setNewToken({ ...newToken, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Production Script"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expires At (optional)
                </label>
                <input
                  type="datetime-local"
                  value={newToken.expires_at}
                  onChange={(e) => setNewToken({ ...newToken, expires_at: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    createMutation.mutate(newToken)
                  }}
                  disabled={!newToken.name || createMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewToken({ name: '', scopes: [], expires_at: '' })
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: '' })}
        onConfirm={(reason) => {
          if (confirmModal.token) {
            if (confirmModal.action === 'revoke') {
              revokeMutation.mutate({ tokenId: confirmModal.token.id, reason })
            } else if (confirmModal.action === 'rotate') {
              rotateMutation.mutate({ tokenId: confirmModal.token.id, reason })
            }
          }
        }}
        title={confirmModal.action === 'revoke' ? 'Revoke Token' : 'Rotate Token'}
        message={
          confirmModal.action === 'revoke'
            ? 'Are you sure you want to revoke this token? This action cannot be undone.'
            : 'Are you sure you want to rotate this token? The old token will be invalidated.'
        }
        confirmText={confirmModal.action === 'revoke' ? 'Revoke' : 'Rotate'}
        requireReason
        variant="danger"
      />
    </div>
  )
}

