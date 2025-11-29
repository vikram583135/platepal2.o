import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
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
    <div className="min-h-screen page-background p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-zomato-dark">Settings</h1>
        <p className="text-zomato-gray mt-1">Manage your restaurant settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Onboarding Status Card - Only show if onboarding is incomplete */}
        {restaurant && restaurant.onboarding_status !== 'APPROVED' && (
          <Card className="bg-gradient-to-br from-red-50 to-orange-50 border-red-200">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-zomato-dark flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-zomato-red" />
                Complete Your Onboarding
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-zomato-gray">
                  {restaurant.onboarding_status === 'NOT_STARTED' && 'Get started with your restaurant setup to begin accepting orders.'}
                  {restaurant.onboarding_status === 'IN_PROGRESS' && 'Continue setting up your restaurant to start accepting orders.'}
                  {restaurant.onboarding_status === 'SUBMITTED' && 'Your application is under review. We\'ll notify you once approved.'}
                  {restaurant.onboarding_status === 'REVISIONS_REQUIRED' && 'Please review and update your information.'}
                </p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-white rounded-full h-2">
                    <div
                      className="bg-zomato-red h-2 rounded-full transition-all"
                      style={{
                        width: restaurant.onboarding_status === 'NOT_STARTED' ? '0%' :
                          restaurant.onboarding_status === 'IN_PROGRESS' ? '50%' :
                            restaurant.onboarding_status === 'SUBMITTED' ? '75%' : '25%'
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-zomato-gray">
                    {restaurant.onboarding_status === 'NOT_STARTED' ? '0%' :
                      restaurant.onboarding_status === 'IN_PROGRESS' ? '50%' :
                        restaurant.onboarding_status === 'SUBMITTED' ? '75%' : '25%'}
                  </span>
                </div>
                {restaurant.onboarding_status !== 'SUBMITTED' && (
                  <Button
                    className="w-full bg-zomato-red hover:bg-zomato-darkRed text-white"
                    onClick={() => window.location.href = '/onboarding'}
                  >
                    {restaurant.onboarding_status === 'NOT_STARTED' ? 'Start Onboarding' : 'Continue Onboarding'}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

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
      </div>
    </div>
  )
}
