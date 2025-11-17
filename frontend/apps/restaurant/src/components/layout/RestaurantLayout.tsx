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

  const { isLoading } = useQuery({
    queryKey: ['my-restaurants'],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/restaurants/')
      return response.data.results || response.data
    },
    onSuccess: (data) => {
      if (Array.isArray(data)) {
        setRestaurants(data)
      }
    },
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  const { data: dashboardSnapshot } = useQuery({
    queryKey: ['dashboard', selectedRestaurantId],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/dashboard/overview/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
    refetchInterval: false, // Disable auto-refetch to avoid 429
  })

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
      // Update store
      setOnlineStatus(data.is_online)
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: ['dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['my-restaurants'] })
      // Update the dashboard snapshot optimistically
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
      // Show user-friendly error
      alert(`Failed to ${dashboardSnapshot?.restaurant?.is_online ? 'go offline' : 'go online'}. Please try again.`)
    },
  })

  // Auto-select first restaurant if we have restaurants but none selected
  // Use useEffect to avoid calling setState during render
  // MUST be called before any conditional returns (Rules of Hooks)
  useEffect(() => {
    if (!selectedRestaurantId && restaurants.length > 0) {
      const approvedRestaurant = restaurants.find((r: any) => r.onboarding_status === 'APPROVED')
      const restaurantToSelect = approvedRestaurant || restaurants[0]
      if (restaurantToSelect?.id) {
        setSelectedRestaurant(restaurantToSelect.id)
      }
    }
  }, [selectedRestaurantId, restaurants, setSelectedRestaurant])

  useRestaurantSocket(selectedRestaurantId)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin h-8 w-8 rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    )
  }

  // Don't redirect to onboarding if we have restaurants but just need to select one
  // Only redirect if we truly have no restaurants at all
  if (!selectedRestaurantId && restaurants.length === 0 && !isLoading) {
    // Check if restaurants are still loading or if we should wait
    return <Navigate to="/onboarding" replace />
  }

  const isOnline = dashboardSnapshot?.restaurant?.is_online ?? false

  return (
    <div className="min-h-screen bg-zomato-lightGray text-zomato-dark">
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen">
          <TopBar
            restaurants={restaurants}
            selectedRestaurantId={selectedRestaurantId}
            onChangeRestaurant={setSelectedRestaurant}
            isOnline={isOnline}
            toggleOnline={() => toggleOnlineMutation.mutate()}
            togglingOnline={toggleOnlineMutation.isPending}
          />
          <main className="flex-1 px-4 py-6 sm:px-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}


