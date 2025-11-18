import { create } from 'zustand'
import type { Restaurant as ApiRestaurant } from '@/packages/types'

export type RestaurantSummary = ApiRestaurant & {
  status?: string
  onboarding_status?: string
  cuisine_types?: string[]
  delivery_radius_km?: number
  is_online?: boolean
}

interface RestaurantState {
  restaurants: RestaurantSummary[]
  selectedRestaurantId: number | null
  setRestaurants: (restaurants: RestaurantSummary[]) => void
  setSelectedRestaurant: (restaurantId: number) => void
  setOnlineStatus: (isOnline: boolean) => void
  clear: () => void
}

export const useRestaurantStore = create<RestaurantState>((set, get) => ({
  restaurants: [],
  selectedRestaurantId: null,
  setRestaurants: (restaurants) =>
    set((state) => {
      // Auto-select first approved restaurant, or first restaurant if none approved
      const approvedRestaurant = restaurants.find((r) => r.onboarding_status === 'APPROVED')
      const restaurantToSelect = approvedRestaurant || restaurants[0]
      const newSelectedId = state.selectedRestaurantId ?? restaurantToSelect?.id ?? null
      
      // Validate that the currently selected restaurant still exists in the new list
      const selectedExists = newSelectedId && restaurants.some((r) => r.id === newSelectedId)
      const finalSelectedId = selectedExists ? newSelectedId : (restaurantToSelect?.id ?? null)
      
      return {
        restaurants,
        selectedRestaurantId: finalSelectedId,
      }
    }),
  setSelectedRestaurant: (restaurantId) => {
    const restaurants = get().restaurants
    const exists = restaurants.find((restaurant) => restaurant.id === restaurantId)
    if (exists) {
      set({ selectedRestaurantId: restaurantId })
    } else {
      console.warn(`Restaurant with ID ${restaurantId} not found in restaurant list. Auto-selecting first available.`)
      // Auto-select first approved restaurant, or first restaurant if none approved
      const approvedRestaurant = restaurants.find((r) => r.onboarding_status === 'APPROVED')
      const restaurantToSelect = approvedRestaurant || restaurants[0]
      if (restaurantToSelect?.id) {
        set({ selectedRestaurantId: restaurantToSelect.id })
      }
    }
  },
  setOnlineStatus: (isOnline) =>
    set((state) => ({
      restaurants: state.restaurants.map((restaurant) =>
        restaurant.id === state.selectedRestaurantId ? { ...restaurant, is_online: isOnline } : restaurant
      ),
    })),
  clear: () => set({ restaurants: [], selectedRestaurantId: null }),
}))

export const useActiveRestaurant = () =>
  useRestaurantStore((state) =>
    state.restaurants.find((restaurant) => restaurant.id === state.selectedRestaurantId) ?? null
  )
