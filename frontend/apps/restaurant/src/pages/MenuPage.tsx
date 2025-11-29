import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'
import { Edit, Plus, X, Image as ImageIcon, Settings, Trash2 } from 'lucide-react'
import { cn } from '@/packages/utils/cn'

export default function MenuPage() {
  const queryClient = useQueryClient()
  const { selectedRestaurantId } = useRestaurantStore()
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null)
  const [activeCategoryId, setActiveCategoryId] = useState<number | null>(null)
  const [newItem, setNewItem] = useState({ name: '', price: '', description: '', category: '' })
  const [formError, setFormError] = useState('')
  const [editingItem, setEditingItem] = useState<any>(null)
  const [newModifier, setNewModifier] = useState({ name: '', price: '', type: 'ADDON', is_required: false })

  const restaurantQuery = useQuery({
    queryKey: ['restaurant-detail', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get(`/restaurants/restaurants/${selectedRestaurantId}/`)
      return response.data
    },
    enabled: Boolean(selectedRestaurantId),
    refetchOnWindowFocus: false, // Disable refetch on window focus to avoid 429
  })

  useEffect(() => {
    const data = restaurantQuery.data as any
    if (data && !activeMenuId && data.menus?.length) {
      setActiveMenuId(data.menus[0].id)
      setActiveCategoryId(data.menus[0].categories?.[0]?.id ?? null)
    }
  }, [restaurantQuery.data, activeMenuId])

  const toggleItemMutation = useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: Record<string, unknown> }) => {
      await apiClient.patch(`/restaurants/items/${itemId}/`, data)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['restaurant-detail', selectedRestaurantId] }),
    onError: (error: any) => {
      console.error('Failed to update item:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update item'
      alert(errorMsg)
    },
  })

  const addItemMutation = useMutation({
    mutationFn: async () => {
      if (!newItem.name.trim()) {
        throw new Error('Item name is required')
      }
      if (!newItem.price || Number(newItem.price) <= 0) {
        throw new Error('Valid price is required')
      }
      if (!newItem.category) {
        throw new Error('Category is required')
      }

      await apiClient.post('/restaurants/items/', {
        name: newItem.name.trim(),
        description: newItem.description.trim(),
        price: Number(newItem.price),
        category: Number(newItem.category),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail', selectedRestaurantId] })
      setNewItem({ name: '', price: '', description: '', category: '' })
      setFormError('')
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to add item'
      setFormError(errorMsg)
      console.error('Failed to add item:', error)
    },
  })

  const handleAddItem = () => {
    setFormError('')

    if (!newItem.name.trim()) {
      setFormError('Item name is required')
      return
    }
    if (!newItem.price || Number(newItem.price) <= 0) {
      setFormError('Valid price is required')
      return
    }
    if (!newItem.category) {
      setFormError('Please select a category')
      return
    }

    addItemMutation.mutate()
  }

  const addModifierMutation = useMutation({
    mutationFn: async ({ itemId, modifier }: { itemId: number; modifier: any }) => {
      await apiClient.post('/restaurants/modifiers/', { ...modifier, menu_item: itemId })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail', selectedRestaurantId] })
      setNewModifier({ name: '', price: '', type: 'ADDON', is_required: false })
    },
    onError: (error: any) => {
      console.error('Failed to add modifier:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to add modifier'
      alert(errorMsg)
    },
  })

  const deleteModifierMutation = useMutation({
    mutationFn: async (modifierId: number) => {
      await apiClient.delete(`/restaurants/modifiers/${modifierId}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to delete modifier:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to delete modifier'
      alert(errorMsg)
    },
  })

  const updateItemMutation = useMutation({
    mutationFn: async ({ itemId, data }: { itemId: number; data: any }) => {
      await apiClient.patch(`/restaurants/items/${itemId}/`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail', selectedRestaurantId] })
      setEditingItem(null)
    },
    onError: (error: any) => {
      console.error('Failed to update item:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update item'
      alert(errorMsg)
    },
  })

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to manage menu</p>
        </div>
      </div>
    )
  }

  if (restaurantQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-sm text-slate-500">Loading menu…</p>
      </div>
    )
  }

  if (restaurantQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load menu</p>
          <p className="text-zomato-gray text-sm">
            {restaurantQuery.error instanceof Error ? restaurantQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const menus = (restaurantQuery.data as any)?.menus ?? []
  const activeMenu = menus.find((menu: any) => menu.id === activeMenuId) ?? menus[0]
  const activeCategory = activeMenu?.categories?.find((category: any) => category.id === activeCategoryId) ?? activeMenu?.categories?.[0]

  // Get all categories for dropdown
  const allCategories = menus.flatMap((menu: any) => menu.categories || [])

  return (
    <div className="min-h-screen page-background p-6">
      <div className="space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-zomato-dark">Menu Management</h1>
            <p className="text-sm text-zomato-gray mt-1">Manage your menu items, categories, and availability</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="border-zomato-red text-zomato-red hover:bg-zomato-red hover:text-white">
              Import CSV
            </Button>
            <Button variant="outline" className="border-zomato-red text-zomato-red hover:bg-zomato-red hover:text-white">
              Export CSV
            </Button>
          </div>
        </header>

        <div className="grid gap-4 lg:grid-cols-4">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-zomato-dark">Menus</CardTitle>
              <CardDescription className="text-zomato-gray">Breakfast, Lunch, Cloud Kitchen…</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {menus.map((menu: any) => (
                <button
                  key={menu.id}
                  className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${menu.id === activeMenu?.id
                    ? 'border-zomato-red bg-zomato-red text-white'
                    : 'border-gray-200 hover:bg-red-50 text-zomato-dark'
                    }`}
                  onClick={() => {
                    setActiveMenuId(menu.id)
                    setActiveCategoryId(menu.categories?.[0]?.id ?? null)
                  }}
                >
                  {menu.name}
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <CardTitle className="text-zomato-dark">Categories</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {activeMenu?.categories?.map((category: any) => (
                <button
                  key={category.id}
                  className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${category.id === activeCategory?.id
                    ? 'border-zomato-red bg-zomato-red text-white'
                    : 'border-gray-200 hover:bg-red-50 text-zomato-dark'
                    }`}
                  onClick={() => setActiveCategoryId(category.id)}
                >
                  {category.name}
                </button>
              ))}
              {!activeMenu?.categories?.length && <p className="text-xs text-slate-500">No categories yet.</p>}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2 bg-white">
            <CardHeader>
              <CardTitle className="text-zomato-dark">
                {activeCategory ? `${activeCategory.name} items` : 'Items'}
              </CardTitle>
              <CardDescription className="text-zomato-gray">
                {activeCategory?.description || 'Manage availability, prep time, and tags.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeCategory?.items?.map((item: any) => (
                <div key={item.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {item.image_url && (
                          <img src={item.image_url} alt={item.name} className="w-12 h-12 rounded-lg object-cover" />
                        )}
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                          <p className="text-xs text-slate-500">{item.description || 'No description'}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-semibold text-slate-800">₹{Number(item.price).toFixed(0)}</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingItem(item)}
                      >
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        className={
                          item.is_available
                            ? 'bg-green-600 hover:bg-green-700 text-white'
                            : 'bg-zomato-red hover:bg-zomato-darkRed text-white'
                        }
                        onClick={() => toggleItemMutation.mutate({ itemId: item.id, data: { is_available: !item.is_available } })}
                      >
                        {item.is_available ? 'Available' : 'Sold Out'}
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
                    {item.is_vegetarian && <span className="px-2 py-0.5 rounded bg-green-50 text-green-700">Veg</span>}
                    {item.is_vegan && <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">Vegan</span>}
                    {item.is_spicy && <span className="px-2 py-0.5 rounded bg-red-50 text-red-700">Spicy</span>}
                    <span className="px-2 py-0.5 rounded bg-gray-100">Prep {item.preparation_time_minutes}m</span>
                    {item.modifiers?.length > 0 && (
                      <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                        {item.modifiers.length} modifier{item.modifiers.length > 1 ? 's' : ''}
                      </span>
                    )}
                    {item.inventory_count !== null && (
                      <span className={cn('px-2 py-0.5 rounded', item.inventory_count <= item.low_stock_threshold ? 'bg-rose-50 text-rose-600' : 'bg-gray-100')}>
                        {item.inventory_count <= item.low_stock_threshold ? 'Low stock' : `Stock ${item.inventory_count}`}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {!activeCategory?.items?.length && <p className="text-sm text-slate-500">No items yet.</p>}
            </CardContent>
          </Card>
        </div>

        <Card className="shadow-md bg-white">
          <CardHeader>
            <CardTitle className="text-zomato-dark">Quick add item</CardTitle>
            <CardDescription className="text-zomato-gray">Launch specials instantly.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-4">
            <Input placeholder="Dish name" value={newItem.name} onChange={(event) => setNewItem((prev) => ({ ...prev, name: event.target.value }))} />
            <Input
              placeholder="Price"
              type="number"
              value={newItem.price}
              onChange={(event) => setNewItem((prev) => ({ ...prev, price: event.target.value }))}
            />
            <select
              value={newItem.category}
              onChange={(event) => setNewItem((prev) => ({ ...prev, category: event.target.value }))}
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
            >
              <option value="">Select category</option>
              {allCategories.length > 0 ? (
                allCategories.map((category: any) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))
              ) : (
                <option disabled>No categories available. Please create a category first.</option>
              )}
            </select>
            <Button
              className="bg-zomato-red hover:bg-zomato-darkRed text-white"
              disabled={!newItem.name || !newItem.price || !newItem.category || addItemMutation.isPending}
              onClick={handleAddItem}
            >
              {addItemMutation.isPending ? 'Adding…' : 'Add'}
            </Button>
            {formError && (
              <div className="md:col-span-4 text-sm text-red-600 mt-1">{formError}</div>
            )}
          </CardContent>
        </Card>

        {editingItem && (
          <ItemEditorModal
            item={editingItem}
            onClose={() => setEditingItem(null)}
            onUpdate={(data) => updateItemMutation.mutate({ itemId: editingItem.id, data })}
            onAddModifier={(modifier) => addModifierMutation.mutate({ itemId: editingItem.id, modifier })}
            onDeleteModifier={(modifierId) => deleteModifierMutation.mutate(modifierId)}
            newModifier={newModifier}
            setNewModifier={setNewModifier}
          />
        )}
      </div>
    </div>
  )
}

function ItemEditorModal({
  item,
  onClose,
  onUpdate,
  onAddModifier,
  onDeleteModifier,
  newModifier,
  setNewModifier,
}: {
  item: any
  onClose: () => void
  onUpdate: (data: any) => void
  onAddModifier: (modifier: any) => void
  onDeleteModifier: (modifierId: number) => void
  newModifier: any
  setNewModifier: (modifier: any) => void
}) {
  const [formData, setFormData] = useState({
    name: item.name || '',
    description: item.description || '',
    price: item.price || '',
    preparation_time_minutes: item.preparation_time_minutes || 15,
    is_vegetarian: item.is_vegetarian || false,
    is_vegan: item.is_vegan || false,
    is_spicy: item.is_spicy || false,
    calories: item.calories || '',
    inventory_count: item.inventory_count ?? '',
    low_stock_threshold: item.low_stock_threshold || 10,
    is_featured: item.is_featured || false,
  })

  const handleSave = () => {
    onUpdate({
      ...formData,
      price: Number(formData.price),
      preparation_time_minutes: Number(formData.preparation_time_minutes),
      calories: formData.calories ? Number(formData.calories) : null,
      inventory_count: formData.inventory_count ? Number(formData.inventory_count) : null,
      low_stock_threshold: Number(formData.low_stock_threshold),
    })
  }

  const handleAddModifier = () => {
    if (!newModifier.name.trim()) return
    onAddModifier({
      name: newModifier.name.trim(),
      price: Number(newModifier.price) || 0,
      type: newModifier.type,
      is_required: newModifier.is_required,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">Edit Menu Item</CardTitle>
            <Button variant="ghost" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Price (₹)</label>
              <Input
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full p-2 border rounded"
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Prep Time (minutes)</label>
              <Input
                type="number"
                value={formData.preparation_time_minutes}
                onChange={(e) => setFormData({ ...formData, preparation_time_minutes: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Calories</label>
              <Input
                type="number"
                value={formData.calories}
                onChange={(e) => setFormData({ ...formData, calories: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stock Count</label>
              <Input
                type="number"
                value={formData.inventory_count}
                onChange={(e) => setFormData({ ...formData, inventory_count: e.target.value })}
                placeholder="Leave empty for unlimited"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Low Stock Threshold</label>
              <Input
                type="number"
                value={formData.low_stock_threshold}
                onChange={(e) => setFormData({ ...formData, low_stock_threshold: e.target.value })}
              />
            </div>
            <div className="col-span-2 flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_vegetarian}
                  onChange={(e) => setFormData({ ...formData, is_vegetarian: e.target.checked })}
                />
                <span className="text-sm">Vegetarian</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_vegan}
                  onChange={(e) => setFormData({ ...formData, is_vegan: e.target.checked })}
                />
                <span className="text-sm">Vegan</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_spicy}
                  onChange={(e) => setFormData({ ...formData, is_spicy: e.target.checked })}
                />
                <span className="text-sm">Spicy</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                />
                <span className="text-sm">Featured</span>
              </label>
            </div>
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold mb-3">Modifiers & Variants</h3>
            <div className="space-y-2 mb-4">
              {item.modifiers?.map((modifier: any) => (
                <div key={modifier.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <span className="font-medium">{modifier.name}</span>
                    <span className="text-sm text-gray-600 ml-2">
                      {modifier.type} - ₹{Number(modifier.price).toFixed(0)}
                      {modifier.is_required && ' (Required)'}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onDeleteModifier(modifier.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
                  </Button>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-5 gap-2">
              <Input
                placeholder="Modifier name"
                value={newModifier.name}
                onChange={(e) => setNewModifier({ ...newModifier, name: e.target.value })}
                className="col-span-2"
              />
              <Input
                type="number"
                placeholder="Price"
                value={newModifier.price}
                onChange={(e) => setNewModifier({ ...newModifier, price: e.target.value })}
              />
              <select
                value={newModifier.type}
                onChange={(e) => setNewModifier({ ...newModifier, type: e.target.value })}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="ADDON">Add-on</option>
                <option value="VARIANT">Variant</option>
                <option value="CUSTOMIZATION">Customization</option>
              </select>
              <Button
                size="sm"
                onClick={handleAddModifier}
                disabled={!newModifier.name.trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <label className="flex items-center gap-2 mt-2">
              <input
                type="checkbox"
                checked={newModifier.is_required}
                onChange={(e) => setNewModifier({ ...newModifier, is_required: e.target.checked })}
              />
              <span className="text-sm">Required (for variants)</span>
            </label>
          </div>

          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSave} className="bg-zomato-red hover:bg-zomato-darkRed text-white">
              Save Changes
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

