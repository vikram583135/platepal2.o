import { useMemo, useEffect } from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { useRestaurantStore } from '../../stores/restaurantStore'
import { useRestaurantSocket } from '../../hooks/useRestaurantSocket'

export function RestaurantLayout() {
  const queryClient = useQueryClient()
  const { restaurants, setRestaurants, selectedRestaurantId, setSelectedRestaurant, setOnlineStatus } = useRestaurantStore()

  const { data: restaurantsData, isLoading } = useQuery({
    queryKey: ['my-restaurants'],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/restaurants/')
      return response.data.results || response.data
    },
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (restaurantsData && Array.isArray(restaurantsData)) {
      setRestaurants(restaurantsData)
    }
  }, [restaurantsData, setRestaurants])

  const { data: dashboardSnapshot, error: dashboardError } = useQuery({
    queryKey: ['dashboard', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }

      // Validate that restaurant exists in user's restaurants list
      const restaurantExists = restaurants.some((r: any) => r.id === selectedRestaurantId)
      if (!restaurantExists && restaurants.length > 0) {
        console.warn('Selected restaurant not in user\'s restaurants list, auto-selecting first available')
        // Auto-select first approved restaurant or first restaurant
        const approvedRestaurant = restaurants.find((r: any) => r.onboarding_status === 'APPROVED')
        const restaurantToSelect = approvedRestaurant || restaurants[0]
        if (restaurantToSelect?.id) {
          setSelectedRestaurant(restaurantToSelect.id)
          // Retry with the new restaurant
          const response = await apiClient.get('/restaurants/dashboard/overview/', {
            params: { restaurant_id: restaurantToSelect.id },
          })
          return response.data
        }
        throw new Error('No valid restaurant available')
      }

      const response = await apiClient.get('/restaurants/dashboard/overview/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchOnWindowFocus: false,
    refetchInterval: false,
    retry: 1,
    retryDelay: 1000,
  })

  useEffect(() => {
    if (dashboardError) {
      const err = dashboardError as any
      console.error('Dashboard snapshot error:', err)
      if ((err?.response?.status === 404 || err?.response?.status === 403) && restaurants.length > 0) {
        const errorData = err.response?.data
        const errorMessage = errorData?.error || errorData?.details?.detail || ''
        if (errorMessage.includes('Restaurant not found') || errorMessage.includes('access denied') || errorMessage.includes('No Restaurant matches')) {
          console.warn('Restaurant not found or access denied, auto-selecting first available restaurant')
          const approvedRestaurant = restaurants.find((r: any) => r.onboarding_status === 'APPROVED')
          const restaurantToSelect = approvedRestaurant || restaurants[0]
          if (restaurantToSelect?.id) {
            setSelectedRestaurant(restaurantToSelect.id)
          }
        }
      }
    }
  }, [dashboardError, restaurants, setSelectedRestaurant])

  const toggleOnlineMutation = useMutation({
    mutationFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const currentState = dashboardSnapshot?.restaurant?.is_online ?? false
      const desiredState = !currentState
      const response = await apiClient.post('/restaurants/dashboard/online-status/', {
        restaurant_id: selectedRestaurantId,
        is_online: desiredState,
      })
      return response.data
    },
    onSuccess: (data) => {
      setOnlineStatus(data.is_online)
      queryClient.invalidateQueries({ queryKey: ['dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['my-restaurants'] })
      queryClient.setQueryData(['dashboard', selectedRestaurantId], (old: any) => {
        if (!old) return old
        return {
          ...old,
          restaurant: {
            ...old.restaurant,
            is_online: data.is_online,
          },
        }
      })
    },
    onError: (error: any) => {
      console.error('Failed to toggle online status:', error)
      alert(`Failed to ${dashboardSnapshot?.restaurant?.is_online ? 'go offline' : 'go online'}. Please try again.`)
    },
  })

  useEffect(() => {
    if (restaurants.length > 0) {
      const selectedExists = selectedRestaurantId && restaurants.some((r: any) => r.id === selectedRestaurantId)

      if (!selectedRestaurantId || !selectedExists) {
        const approvedRestaurant = restaurants.find((r: any) => r.onboarding_status === 'APPROVED')
        const restaurantToSelect = approvedRestaurant || restaurants[0]
        if (restaurantToSelect?.id) {
          console.log('Auto-selecting restaurant:', restaurantToSelect.id, restaurantToSelect.name)
          setSelectedRestaurant(restaurantToSelect.id)
        }
      }
    }
  }, [selectedRestaurantId, restaurants, setSelectedRestaurant, isLoading])

  useRestaurantSocket(selectedRestaurantId)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100">
        <div className="animate-spin h-8 w-8 rounded-full border-2 border-zomato-red border-t-transparent" />
      </div>
    )
  }

  if (!selectedRestaurantId && restaurants.length === 0 && !isLoading) {
    return <Navigate to="/onboarding" replace />
  }

  const isOnline = dashboardSnapshot?.restaurant?.is_online ?? false

  return (
    <div className="min-h-screen page-background text-zomato-dark">
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen">
          <TopBar
            restaurants={restaurants}
            selectedRestaurantId={selectedRestaurantId}
            isOnline={isOnline}
            toggleOnline={() => toggleOnlineMutation.mutate()}
            togglingOnline={toggleOnlineMutation.isPending}
          />
          <main className="flex-1 px-4 py-6 sm:px-8 page-content">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
