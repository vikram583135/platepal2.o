import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'

export default function InventoryPage() {
  const queryClient = useQueryClient()
  const { selectedRestaurantId } = useRestaurantStore()
  const [restockQuantity, setRestockQuantity] = useState<Record<number, string>>({})

  const inventoryQuery = useQuery({
    queryKey: ['inventory', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/inventory/items/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || [])
    },
    enabled: Boolean(selectedRestaurantId),
    refetchInterval: 30000, // Reduced to avoid 429
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  const restockMutation = useMutation({
    mutationFn: async ({ itemId, quantity }: { itemId: number; quantity: string }) => {
      await apiClient.post(`/inventory/items/${itemId}/restock/`, { quantity: Number(quantity) })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to restock item:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to restock item'
      alert(errorMsg)
    },
  })

  const markSoldOutMutation = useMutation({
    mutationFn: async (itemId: number) => {
      await apiClient.post(`/inventory/items/${itemId}/mark_sold_out/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', selectedRestaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to mark item as sold out:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to mark as sold out'
      alert(errorMsg)
    },
  })

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view inventory</p>
        </div>
      </div>
    )
  }

  if (inventoryQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading inventory...</p>
      </div>
    )
  }

  if (inventoryQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load inventory</p>
          <p className="text-zomato-gray text-sm">
            {inventoryQuery.error instanceof Error ? inventoryQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const inventory = inventoryQuery.data || []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Inventory & stock</h1>
        <p className="text-sm text-slate-500">Stay in sync with the Kitchen Display System and Zomato listing.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {inventory.length > 0 ? (
          inventory.map((item: any) => (
          <Card key={item.id} className="border-white/70 bg-white/90 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-slate-900">{item.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold text-slate-500">Current stock</span>
                <span className={item.is_low_stock ? 'text-rose-600 font-semibold' : 'text-slate-900 font-semibold'}>
                  {Number(item.current_stock || 0).toFixed(2)} {item.unit || 'PC'}
                </span>
              </div>
              <div className="grid grid-cols-6 gap-2 items-center">
                <Input
                  type="number"
                  min={1}
                  value={restockQuantity[item.id] ?? ''}
                  onChange={(event) => setRestockQuantity((prev) => ({ ...prev, [item.id]: event.target.value }))}
                  placeholder="Qty"
                  className="col-span-3"
                />
                <Button
                  size="sm"
                  className="col-span-3"
                  disabled={!restockQuantity[item.id] || restockMutation.isPending}
                  onClick={() => restockMutation.mutate({ itemId: item.id, quantity: restockQuantity[item.id] })}
                >
                  Restock
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => markSoldOutMutation.mutate(item.id)}
                  disabled={markSoldOutMutation.isPending}
                >
                  Mark sold out
                </Button>
                {item.menu_item && (
                  <Button size="sm" variant="ghost" onClick={() => window.location.href = '/menu'}>
                    View dish
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <p className="text-sm text-slate-500">No inventory tracked yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}


