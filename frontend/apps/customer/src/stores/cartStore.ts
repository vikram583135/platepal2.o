import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { MenuItem, ItemModifier } from '@/packages/types'

interface CartItem {
  menuItem: MenuItem
  quantity: number
  selectedModifiers: ItemModifier[]
}

interface CartState {
  items: CartItem[]
  restaurantId: number | null
  isGuest: boolean
  addItem: (item: MenuItem, modifiers?: ItemModifier[], restaurantId?: number) => void
  removeItem: (itemId: number) => void
  updateQuantity: (itemId: number, quantity: number) => void
  clearCart: () => void
  getTotal: () => number
  getItemCount: () => number
  setGuestMode: (isGuest: boolean) => void
}

// Helper function to validate and clean cart items
// Made more lenient to handle various data structures and edge cases
const validateCartItems = (items: any[]): CartItem[] => {
  if (!Array.isArray(items)) {
    if (import.meta.env.DEV) {
      console.warn('validateCartItems: items is not an array', items)
    }
    return []
  }

  const validated: CartItem[] = []
  const invalidItems: any[] = []

  items.forEach((item: any, index: number) => {
    if (!item) {
      invalidItems.push({ index, reason: 'item is null/undefined' })
      return
    }

    // Support multiple formats: menuItem, menu_item
    const menuItem = item.menuItem || item.menu_item
    if (!menuItem) {
      invalidItems.push({ index, reason: 'no menuItem/menu_item', item })
      return
    }

    // Support both object and direct ID
    const menuItemId = typeof menuItem === 'object' ? menuItem.id : menuItem
    if (!menuItemId) {
      invalidItems.push({ index, reason: 'no menuItem.id', menuItem })
      return
    }

    // Validate quantity - be lenient
    let quantity = item.quantity
    if (typeof quantity !== 'number') {
      quantity = parseInt(quantity) || 1
    }
    if (quantity <= 0) {
      quantity = 1
    }

    // Support multiple formats: selectedModifiers, selected_modifiers, modifiers
    const modifiers = item.selectedModifiers || item.selected_modifiers || item.modifiers || []
    const validModifiers = Array.isArray(modifiers)
      ? modifiers.filter((m: any) => m && (m.id || m.modifier_id))
      : []

    // If menuItem is just an ID, we need to reconstruct it
    // For now, accept it if we have at least an ID
    const finalMenuItem = typeof menuItem === 'object'
      ? menuItem
      : { id: menuItemId, price: item.price || 0, name: item.name || 'Item' }

    validated.push({
      menuItem: finalMenuItem,
      quantity: Math.max(1, Math.floor(quantity)),
      selectedModifiers: validModifiers.map((m: any) => ({
        id: m.id || m.modifier_id,
        name: m.name || m.modifier_name || '',
        price: m.price || 0,
        type: m.type || 'ADD_ON',
        is_required: m.is_required || false,
        is_available: m.is_available !== undefined ? m.is_available : true,
        display_order: m.display_order || 0,
      })),
    })
  })

  // Log invalid items in development
  if (import.meta.env.DEV && invalidItems.length > 0) {
    console.warn('validateCartItems: filtered out invalid items', invalidItems)
  }

  return validated
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      restaurantId: null,
      isGuest: false,

      addItem: (menuItem: MenuItem, selectedModifiers: ItemModifier[] = [], restaurantId?: number) => {
        set((state) => {
          // Validate existing items first
          const validatedItems = validateCartItems(state.items || [])

          // Ensure restaurantId is provided when adding first item
          if (!restaurantId && validatedItems.length === 0 && !state.restaurantId) {
            if (import.meta.env.DEV) {
              console.warn('addItem: restaurantId not provided and cart is empty. This may cause issues.')
            }
          }

          // If adding from different restaurant, clear cart
          if (state.restaurantId && restaurantId && state.restaurantId !== restaurantId) {
            // If user confirms (this should be handled in UI, but for safety we clear)
            return {
              items: [{ menuItem, quantity: 1, selectedModifiers }],
              restaurantId: restaurantId,
            }
          }

          // If cart is empty or restaurantId is null, set it
          const newRestaurantId = state.items.length === 0 ? restaurantId : (state.restaurantId || restaurantId)

          const existingIndex = validatedItems.findIndex(
            (item) => item.menuItem.id === menuItem.id
          )

          if (existingIndex >= 0) {
            const updatedItems = [...validatedItems]
            updatedItems[existingIndex].quantity += 1
            // Preserve restaurantId even when updating quantity
            return {
              items: updatedItems,
              restaurantId: restaurantId || state.restaurantId,
            }
          }

          return {
            items: [...validatedItems, { menuItem, quantity: 1, selectedModifiers }],
            restaurantId: newRestaurantId,
          }
        })
      },

      removeItem: (itemId: number) => {
        set((state) => ({
          items: state.items.filter((item) => item.menuItem.id !== itemId),
        }))
      },

      updateQuantity: (itemId: number, quantity: number) => {
        if (quantity <= 0) {
          get().removeItem(itemId)
          return
        }

        set((state) => ({
          items: state.items.map((item) =>
            item.menuItem.id === itemId ? { ...item, quantity } : item
          ),
        }))
      },

      clearCart: () => {
        set({ items: [], restaurantId: null })
      },

      getTotal: () => {
        const state = get()
        const validatedItems = validateCartItems(state.items || [])
        const total = validatedItems.reduce((total, item) => {
          const itemPrice = typeof item.menuItem.price === 'number' ? item.menuItem.price : parseFloat(item.menuItem.price) || 0
          const modifiersPrice = item.selectedModifiers.reduce(
            (sum, mod) => sum + (typeof mod.price === 'number' ? mod.price : parseFloat(mod.price) || 0),
            0
          )
          return total + (itemPrice + modifiersPrice) * item.quantity
        }, 0)

        if (import.meta.env.DEV) {
          console.log('getTotal:', {
            rawItems: state.items?.length || 0,
            validatedItems: validatedItems.length,
            total
          })
        }

        return total
      },

      getItemCount: () => {
        const state = get()
        const validatedItems = validateCartItems(state.items || [])
        const count = validatedItems.reduce((count, item) => count + item.quantity, 0)

        if (import.meta.env.DEV) {
          console.log('getItemCount:', {
            rawItems: state.items?.length || 0,
            validatedItems: validatedItems.length,
            count
          })
        }

        return count
      },

      setGuestMode: (isGuest: boolean) => {
        set({ isGuest })
      },
    }),
    {
      name: 'cart-storage',
      storage: createJSONStorage(() => localStorage),
      // Validate and clean cart items on rehydration
      onRehydrateStorage: () => (state) => {
        if (import.meta.env.DEV) {
          console.log('Cart rehydration:', {
            hasState: !!state,
            itemsCount: state?.items?.length || 0,
            restaurantId: state?.restaurantId
          })
        }

        if (state && state.items) {
          const validatedItems = validateCartItems(state.items)

          if (import.meta.env.DEV) {
            console.log('Cart validation result:', {
              originalCount: state.items.length,
              validatedCount: validatedItems.length,
              filtered: state.items.length - validatedItems.length
            })
          }

          // Check if validation changed anything
          const itemsChanged = validatedItems.length !== state.items.length ||
            validatedItems.some((validItem, index) => {
              const originalItem = state.items[index] as any
              return !originalItem ||
                validItem.menuItem.id !== (originalItem.menuItem?.id || originalItem.menu_item?.id || originalItem.menu_item) ||
                validItem.quantity !== originalItem.quantity
            })

          if (itemsChanged) {
            if (import.meta.env.DEV) {
              console.log('Updating cart with validated items', { itemsChanged, originalRestaurantId: state.restaurantId })
            }
            // Update store with validated items directly
            // Preserve restaurantId if items exist, clear if no items
            setTimeout(() => {
              useCartStore.setState({
                items: validatedItems,
                restaurantId: validatedItems.length > 0 ? state.restaurantId : null,
              })
            }, 0)
          }
        }
      },
    }
  )
)

