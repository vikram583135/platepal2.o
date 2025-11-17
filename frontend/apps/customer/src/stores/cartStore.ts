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

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      restaurantId: null,
      isGuest: false,

      addItem: (menuItem: MenuItem, selectedModifiers: ItemModifier[] = [], restaurantId?: number) => {
        set((state) => {
          // If adding from different restaurant, clear cart
          if (state.restaurantId && restaurantId && state.restaurantId !== restaurantId) {
            return {
              items: [{ menuItem, quantity: 1, selectedModifiers }],
              restaurantId: restaurantId,
            }
          }

          const existingIndex = state.items.findIndex(
            (item) => item.menuItem.id === menuItem.id
          )

          if (existingIndex >= 0) {
            const updatedItems = [...state.items]
            updatedItems[existingIndex].quantity += 1
            return { items: updatedItems }
          }

          return {
            items: [...state.items, { menuItem, quantity: 1, selectedModifiers }],
            restaurantId: restaurantId || state.restaurantId,
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
        return get().items.reduce((total, item) => {
          const itemPrice = item.menuItem.price
          const modifiersPrice = item.selectedModifiers.reduce(
            (sum, mod) => sum + mod.price,
            0
          )
          return total + (itemPrice + modifiersPrice) * item.quantity
        }, 0)
      },

      getItemCount: () => {
        return get().items.reduce((count, item) => count + item.quantity, 0)
      },
      
      setGuestMode: (isGuest: boolean) => {
        set({ isGuest })
      },
    }),
    {
      name: 'cart-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

