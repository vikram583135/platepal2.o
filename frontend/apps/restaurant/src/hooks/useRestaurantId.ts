import { useRestaurantStore } from '../stores/restaurantStore'

export function useRestaurantId() {
  return useRestaurantStore((state) => state.selectedRestaurantId)
}

