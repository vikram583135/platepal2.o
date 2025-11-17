import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'
import { Search, Filter } from 'lucide-react'

interface Order {
  id: number
  order_number: string
  customer: { email: string; first_name: string; last_name: string }
  restaurant: { name: string }
  status: string
  total_amount: string
  created_at: string
  order_type: string
}

export default function OrdersPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: orders, isLoading } = useQuery({
    queryKey: ['admin-orders', searchQuery, statusFilter],
    queryFn: async () => {
      const params: any = {}
      if (searchQuery) params.search = searchQuery
      if (statusFilter) params.status = statusFilter
      const response = await apiClient.get('/orders/', { params })
      return response.data.results || response.data
    },
  })

  const columns: Column<Order>[] = [
    {
      key: 'order_number',
      header: 'Order Number',
      accessor: (row) => (
        <button
          onClick={() => navigate(`/orders/${row.id}`)}
          className="text-blue-600 hover:underline"
        >
          {row.order_number}
        </button>
      ),
      sortable: true,
    },
    {
      key: 'customer',
      header: 'Customer',
      accessor: (row) => row.customer?.email || 'N/A',
      sortable: true,
    },
    {
      key: 'restaurant',
      header: 'Restaurant',
      accessor: (row) => row.restaurant?.name || 'N/A',
      sortable: true,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.status === 'DELIVERED' ? 'bg-green-100 text-green-800' :
          row.status === 'CANCELLED' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'total_amount',
      header: 'Total',
      accessor: (row) => `$${parseFloat(row.total_amount).toFixed(2)}`,
      sortable: true,
    },
    {
      key: 'created_at',
      header: 'Date',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-600">Manage and track all orders</p>
        </div>
        <CSVExporter
          data={orders || []}
          filename={`orders-${new Date().toISOString().split('T')[0]}.csv`}
        />
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search orders..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="ACCEPTED">Accepted</option>
          <option value="PREPARING">Preparing</option>
          <option value="DELIVERED">Delivered</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <DataTable
        data={orders || []}
        columns={columns}
        loading={isLoading}
        searchable={false}
        pageSize={20}
      />
    </div>
  )
}

