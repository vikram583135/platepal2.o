import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'

interface Restaurant {
  id: number
  name: string
  owner: { email: string }
  cuisine_type: string
  status: string
  rating: number
  city: string
  kyc_verified: boolean
}

export default function RestaurantsPage() {
  const navigate = useNavigate()

  const { data: restaurants, isLoading } = useQuery({
    queryKey: ['admin-restaurants'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/management/restaurants/')
      return response.data.results || response.data
    },
  })

  const columns: Column<Restaurant>[] = [
    {
      key: 'name',
      header: 'Restaurant',
      accessor: (row) => (
        <button
          onClick={() => navigate(`/restaurants/${row.id}`)}
          className="text-blue-600 hover:underline font-medium"
        >
          {row.name}
        </button>
      ),
      sortable: true,
    },
    {
      key: 'owner',
      header: 'Owner',
      accessor: (row) => row.owner?.email || 'N/A',
      sortable: true,
    },
    {
      key: 'cuisine',
      header: 'Cuisine',
      accessor: (row) => row.cuisine_type,
      sortable: true,
    },
    {
      key: 'rating',
      header: 'Rating',
      accessor: (row) => `${row.rating}/5`,
      sortable: true,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
          row.status === 'SUSPENDED' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'kyc',
      header: 'KYC',
      accessor: (row) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          row.kyc_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
        }`}>
          {row.kyc_verified ? 'Verified' : 'Pending'}
        </span>
      ),
    },
    {
      key: 'city',
      header: 'City',
      accessor: (row) => row.city,
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Restaurants</h1>
          <p className="text-gray-600">Manage restaurant accounts and onboarding</p>
        </div>
        <CSVExporter
          data={restaurants || []}
          filename={`restaurants-${new Date().toISOString().split('T')[0]}.csv`}
        />
      </div>

      <DataTable
        data={restaurants || []}
        columns={columns}
        loading={isLoading}
        searchable
        pageSize={20}
      />
    </div>
  )
}

