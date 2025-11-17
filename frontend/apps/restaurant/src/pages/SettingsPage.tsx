import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Settings as SettingsIcon, AlertCircle } from 'lucide-react'
import { useRestaurantStore } from '../stores/restaurantStore'

export default function SettingsPage() {
  const { selectedRestaurantId } = useRestaurantStore()

  const { data: restaurant, isLoading, error } = useQuery({
    queryKey: ['restaurant-profile', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get(`/restaurants/restaurants/${selectedRestaurantId}/`)
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
  })

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view settings</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading settings...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Failed to load settings</p>
          <p className="text-zomato-gray text-sm">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zomato-lightGray p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zomato-dark">Settings</h1>
        <p className="text-zomato-gray mt-1">Manage your restaurant settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-zomato-dark">Restaurant Information</CardTitle>
          </CardHeader>
          <CardContent>
            {restaurant ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-zomato-gray">Restaurant Name</label>
                  <p className="text-zomato-dark font-semibold">{restaurant.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zomato-gray">Cuisine Type</label>
                  <p className="text-zomato-dark">{restaurant.cuisine_type}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zomato-gray">Location</label>
                  <p className="text-zomato-dark">
                    {restaurant.address}, {restaurant.city}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-zomato-gray">Loading...</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-zomato-dark">Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-16 text-zomato-gray">
              <SettingsIcon className="h-16 w-16 mx-auto mb-4 text-zomato-gray opacity-50" />
              <p className="text-lg">Settings management coming soon</p>
              <p className="text-sm mt-2">
                Configure delivery radius, prep times, notifications, and more
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
