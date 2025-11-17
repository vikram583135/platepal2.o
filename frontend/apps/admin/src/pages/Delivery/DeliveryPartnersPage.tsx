import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { Truck, Shield } from 'lucide-react'

interface DeliveryPartner {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  date_joined: string
}

export default function DeliveryPartnersPage() {
  const { data: partners, isLoading } = useQuery({
    queryKey: ['delivery-partners'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/management/delivery/')
      return response.data.results || response.data
    },
  })

  const columns: Column<DeliveryPartner>[] = [
    {
      key: 'name',
      header: 'Name',
      accessor: (row) => `${row.first_name} ${row.last_name}`.trim() || row.email,
      sortable: true,
    },
    {
      key: 'email',
      header: 'Email',
      accessor: (row) => row.email,
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
      key: 'date_joined',
      header: 'Joined',
      accessor: (row) => new Date(row.date_joined).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Delivery Partners</h1>
        <p className="text-gray-600">Manage delivery rider accounts</p>
      </div>

      <DataTable
        data={partners || []}
        columns={columns}
        loading={isLoading}
        searchable
        pageSize={20}
      />
    </div>
  )
}

