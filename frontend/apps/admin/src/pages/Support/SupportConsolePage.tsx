import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { MessageSquare, AlertCircle } from 'lucide-react'

interface SupportTicket {
  id: number
  ticket_number: string
  user: { email: string }
  subject: string
  status: string
  priority: string
  category: string
  created_at: string
}

export default function SupportConsolePage() {
  const { data: tickets, isLoading } = useQuery({
    queryKey: ['support-tickets'],
    queryFn: async () => {
      const response = await apiClient.get('/support/tickets/')
      return response.data.results || response.data
    },
  })

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'URGENT':
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
      case 'IN_PROGRESS':
        return 'bg-yellow-100 text-yellow-800'
      case 'RESOLVED':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const columns: Column<SupportTicket>[] = [
    {
      key: 'ticket_number',
      header: 'Ticket #',
      accessor: (row) => (
        <code className="text-sm">{row.ticket_number}</code>
      ),
      sortable: true,
    },
    {
      key: 'user',
      header: 'User',
      accessor: (row) => row.user?.email || 'N/A',
      sortable: true,
    },
    {
      key: 'subject',
      header: 'Subject',
      accessor: (row) => row.subject,
      sortable: true,
    },
    {
      key: 'category',
      header: 'Category',
      accessor: (row) => (
        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
          {row.category.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'priority',
      header: 'Priority',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(row.priority)}`}>
          {row.priority}
        </span>
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
      key: 'created_at',
      header: 'Created',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Support Console</h1>
        <p className="text-gray-600">Manage customer support tickets</p>
      </div>

      <DataTable
        data={tickets || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />
    </div>
  )
}

