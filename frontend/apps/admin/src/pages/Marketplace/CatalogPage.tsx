import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Star } from 'lucide-react'

export default function CatalogPage() {
  const { data: categories } = useQuery({
    queryKey: ['catalog-categories'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/catalog/categories/')
      return response.data
    },
  })

  const { data: featured } = useQuery({
    queryKey: ['featured-restaurants'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/catalog/featured_listings/')
      return response.data
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Catalog Management</h1>
        <p className="text-gray-600">Manage categories, taxonomies, and featured listings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Menu Categories</CardTitle>
          </CardHeader>
          <CardContent>
            {categories ? (
              <div className="space-y-4">
                {Object.entries(categories).map(([restaurant, cats]: [string, any]) => (
                  <div key={restaurant} className="border-b pb-4 last:border-0">
                    <h3 className="font-semibold mb-2">{restaurant}</h3>
                    <div className="space-y-1">
                      {cats.map((cat: any) => (
                        <div key={cat.id} className="flex items-center justify-between text-sm">
                          <span>{cat.name}</span>
                          <span className={`px-2 py-1 text-xs rounded ${
                            cat.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {cat.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No categories found</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Featured Restaurants</CardTitle>
          </CardHeader>
          <CardContent>
            {featured && featured.length > 0 ? (
              <div className="space-y-2">
                {featured.map((restaurant: any) => (
                  <div key={restaurant.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      <span className="font-medium">{restaurant.name}</span>
                    </div>
                    <span className="text-sm text-gray-600">{restaurant.rating}/5</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No featured restaurants</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

