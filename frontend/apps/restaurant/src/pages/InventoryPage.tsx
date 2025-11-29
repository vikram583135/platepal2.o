import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'
import { AlertCircle, CheckCircle2, Power, PowerOff } from 'lucide-react'

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
    refetchInterval: 30000,
    refetchOnWindowFocus: false,
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

  const toggleAutoDisableMutation = useMutation({
    mutationFn: async ({ itemId, autoMarkUnavailable }: { itemId: number; autoMarkUnavailable: boolean }) => {
      await apiClient.patch(`/inventory/items/${itemId}/`, { auto_mark_unavailable: autoMarkUnavailable })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to toggle auto-disable:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update setting'
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
        <h1 className="text-3xl font-bold text-slate-900">Inventory & Stock</h1>
        <p className="text-sm text-slate-500">Stay in sync with the Kitchen Display System and Zomato listing.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {inventory.length > 0 ? (
          inventory.map((item: any) => {
            const isLowStock = item.is_low_stock || Number(item.current_stock || 0) <= Number(item.low_stock_threshold || 0)
            const isOutOfStock = Number(item.current_stock || 0) === 0
            const wasAutoDisabled = item.last_auto_disabled_at && item.auto_mark_unavailable

            return (
              <Card key={item.id} className={`border-white/70 bg-white/90 shadow-sm ${isOutOfStock ? 'border-l-4 border-l-red-500' : isLowStock ? 'border-l-4 border-l-orange-500' : ''}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base font-semibold text-slate-900">{item.name}</CardTitle>
                    {wasAutoDisabled && (
                      <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full flex items-center gap-1">
                        <PowerOff className="h-3 w-3" />
                        Auto-disabled
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-slate-500">Current stock</span>
                    <span className={`font-semibold ${isOutOfStock ? 'text-red-600' : isLowStock ? 'text-orange-600' : 'text-slate-900'}`}>
                      {Number(item.current_stock || 0).toFixed(2)} {item.unit || 'PC'}
                    </span>
                  </div>

                  {isLowStock && !isOutOfStock && (
                    <div className="flex items-center gap-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                      <AlertCircle className="h-4 w-4" />
                      <span>Low stock alert</span>
                    </div>
                  )}

                  {isOutOfStock && (
                    <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                      <AlertCircle className="h-4 w-4" />
                      <span>Out of stock</span>
                    </div>
                  )}

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

                  <div className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs">
                    <div className="flex items-center gap-2">
                      {item.auto_mark_unavailable ? (
                        <Power className="h-3 w-3 text-green-600" />
                      ) : (
                        <PowerOff className="h-3 w-3 text-gray-400" />
                      )}
                      <span className="text-slate-700">Auto-disable when out</span>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-6 px-2"
                      onClick={() => toggleAutoDisableMutation.mutate({
                        itemId: item.id,
                        autoMarkUnavailable: !item.auto_mark_unavailable
                      })}
                      disabled={toggleAutoDisableMutation.isPending}
                    >
                      {item.auto_mark_unavailable ? 'Disable' : 'Enable'}
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
            )
          })
        ) : (
          <div className="col-span-full text-center py-12">
            <p className="text-sm text-slate-500">No inventory tracked yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}

