import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Star, Edit } from 'lucide-react'

interface Restaurant {
  id: number
  name: string
  description: string
  cuisine_type: string
  rating: number
  status: string
  is_featured?: boolean
}

export default function RestaurantContentPage() {
  const queryClient = useQueryClient()
  const [editingRestaurant, setEditingRestaurant] = useState<Restaurant | null>(null)
  const [description, setDescription] = useState('')

  const { data: restaurants, isLoading } = useQuery({
    queryKey: ['restaurants-content'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/management/restaurants/')
      return response.data.results || response.data
    },
  })

  const updateDescriptionMutation = useMutation({
    mutationFn: async ({ restaurantId, description, reason }: { restaurantId: number; description: string; reason?: string }) => {
      return apiClient.post(`/admin/content/restaurants/${restaurantId}/update_description/`, { description, reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurants-content'] })
      setEditingRestaurant(null)
      setDescription('')
    },
  })

  const featureMutation = useMutation({
    mutationFn: async ({ restaurantId, reason }: { restaurantId: number; reason?: string }) => {
      return apiClient.post(`/admin/content/restaurants/${restaurantId}/feature/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurants-content'] })
    },
  })

  const handleEdit = (restaurant: Restaurant) => {
    setEditingRestaurant(restaurant)
    setDescription(restaurant.description)
  }

  const handleSave = () => {
    if (editingRestaurant) {
      updateDescriptionMutation.mutate({
        restaurantId: editingRestaurant.id,
        description,
        reason: 'Content update'
      })
    }
  }

  const columns: Column<Restaurant>[] = [
    {
      key: 'name',
      header: 'Restaurant',
      accessor: (row) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{row.name}</span>
          {row.is_featured && <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />}
        </div>
      ),
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
      key: 'description',
      header: 'Description',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.description}>
          {row.description || 'No description'}
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => handleEdit(row)}
            className="p-1 text-blue-600 hover:bg-blue-50 rounded"
          >
            <Edit className="w-4 h-4" />
          </button>
          {!row.is_featured && (
            <button
              onClick={() => featureMutation.mutate({ restaurantId: row.id, reason: 'Featured by admin' })}
              className="p-1 text-yellow-600 hover:bg-yellow-50 rounded"
            >
              <Star className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Restaurant Content Management</h1>
        <p className="text-gray-600">Manage restaurant descriptions and featured listings</p>
      </div>

      <DataTable
        data={restaurants || []}
        columns={columns}
        loading={isLoading}
        pageSize={20}
      />

      {editingRestaurant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <Card className="max-w-2xl w-full mx-4">
            <CardHeader>
              <CardTitle>Edit Description: {editingRestaurant.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={updateDescriptionMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditingRestaurant(null)
                    setDescription('')
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
    </div>
  )
}

