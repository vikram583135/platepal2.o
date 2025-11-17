import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'
import { Plus, Ban, Unlock, Key, Download } from 'lucide-react'

interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  is_email_verified: boolean
  date_joined: string
  phone?: string
}

export default function UsersPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedUsers, setSelectedUsers] = useState<User[]>([])
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    action: string
    user?: User
    users?: User[]
  }>({ isOpen: false, action: '' })

  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/management/users/')
      return response.data.results || response.data
    },
  })

  const banMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason?: string }) => {
      return apiClient.post(`/admin/management/users/${userId}/ban/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const unbanMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason?: string }) => {
      return apiClient.post(`/admin/management/users/${userId}/unban/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: number; reason?: string }) => {
      return apiClient.post(`/admin/management/users/${userId}/reset-password/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const handleBulkAction = (action: string) => {
    if (selectedUsers.length === 0) return
    setConfirmModal({ isOpen: true, action, users: selectedUsers })
  }

  const handleConfirm = (reason?: string) => {
    const { action, user, users } = confirmModal
    const targetUsers = user ? [user] : users || []

    if (action === 'ban') {
      targetUsers.forEach(u => {
        banMutation.mutate({ userId: u.id, reason })
      })
    } else if (action === 'unban') {
      targetUsers.forEach(u => {
        unbanMutation.mutate({ userId: u.id, reason })
      })
    } else if (action === 'reset-password') {
      targetUsers.forEach(u => {
        resetPasswordMutation.mutate({ userId: u.id, reason })
      })
    }
  }

  const columns: Column<User>[] = [
    {
      key: 'email',
      header: 'Email',
      accessor: (row) => row.email,
      sortable: true,
    },
    {
      key: 'name',
      header: 'Name',
      accessor: (row) => `${row.first_name} ${row.last_name}`.trim() || 'N/A',
      sortable: true,
    },
    {
      key: 'role',
      header: 'Role',
      accessor: (row) => (
        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
          {row.role}
        </span>
      ),
      sortable: true,
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
      key: 'verified',
      header: 'Verified',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.is_email_verified ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {row.is_email_verified ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      key: 'date_joined',
      header: 'Joined',
      accessor: (row) => new Date(row.date_joined).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <p className="text-gray-600">Manage customer accounts</p>
        </div>
        <div className="flex items-center gap-2">
          {selectedUsers.length > 0 && (
            <>
              <button
                onClick={() => handleBulkAction('ban')}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                <Ban className="w-4 h-4" />
                Ban Selected
              </button>
              <button
                onClick={() => handleBulkAction('unban')}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Unlock className="w-4 h-4" />
                Unban Selected
              </button>
            </>
          )}
          <CSVExporter
            data={users || []}
            filename={`users-${new Date().toISOString().split('T')[0]}.csv`}
          />
        </div>
      </div>

      <DataTable
        data={users || []}
        columns={columns}
        loading={isLoading}
        onRowClick={(user) => navigate(`/users/${user.id}`)}
        selectedRows={selectedUsers}
        onSelectionChange={setSelectedUsers}
        searchable
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: '' })}
        onConfirm={handleConfirm}
        title={
          confirmModal.action === 'ban' ? 'Ban User(s)' :
          confirmModal.action === 'unban' ? 'Unban User(s)' :
          'Reset Password'
        }
        message={
          confirmModal.action === 'ban' 
            ? `Are you sure you want to ban ${confirmModal.user ? 'this user' : `${confirmModal.users?.length} users`}?`
            : confirmModal.action === 'unban'
            ? `Are you sure you want to unban ${confirmModal.user ? 'this user' : `${confirmModal.users?.length} users`}?`
            : `Are you sure you want to reset the password for ${confirmModal.user ? 'this user' : `${confirmModal.users?.length} users`}?`
        }
        confirmText={confirmModal.action === 'ban' ? 'Ban' : confirmModal.action === 'unban' ? 'Unban' : 'Reset'}
        requireReason
        variant={confirmModal.action === 'ban' ? 'danger' : 'warning'}
      />
    </div>
  )
}

