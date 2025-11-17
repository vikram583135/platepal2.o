import { useState } from 'react'
import { X, ShoppingCart, AlertTriangle } from 'lucide-react'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { formatCurrency } from '@/packages/utils/format'
import NutritionInfo from './NutritionInfo'

interface ItemDetailModalProps {
  item: any
  isOpen: boolean
  onClose: () => void
  onAddToCart: (item: any, modifiers: any[], quantity: number) => void
  restaurantId: number
}

export default function ItemDetailModal({ item, isOpen, onClose, onAddToCart, restaurantId }: ItemDetailModalProps) {
  const [selectedModifiers, setSelectedModifiers] = useState<any[]>([])
  const [quantity, setQuantity] = useState(1)
  const [specialInstructions, setSpecialInstructions] = useState('')

  if (!isOpen || !item) return null

  const handleModifierToggle = (modifier: any) => {
    // Grouped modifiers (size, spice level) - only one per group
    if (modifier.group) {
      setSelectedModifiers(prev => {
        const filtered = prev.filter(m => m.group !== modifier.group)
        return [...filtered, modifier]
      })
    } else if (modifier.is_required || modifier.type === 'SIZE' || modifier.type === 'SPICE_LEVEL') {
      // Required modifiers or size/spice - replace if same type
      setSelectedModifiers(prev => {
        const filtered = prev.filter(m => m.type !== modifier.type && m.group !== modifier.group)
        return [...filtered, modifier]
      })
    } else {
      // Optional modifiers - toggle
      setSelectedModifiers(prev => {
        const exists = prev.find(m => m.id === modifier.id)
        if (exists) {
          return prev.filter(m => m.id !== modifier.id)
        } else {
          return [...prev, modifier]
        }
      })
    }
  }

  // Group modifiers by group or type
  const groupedModifiers = item.modifiers?.reduce((acc: any, modifier: any) => {
    const key = modifier.group || modifier.type || 'other'
    if (!acc[key]) {
      acc[key] = []
    }
    acc[key].push(modifier)
    return acc
  }, {}) || {}

  const calculateTotal = () => {
    const itemPrice = parseFloat(item.price) || 0
    const modifiersPrice = selectedModifiers.reduce((sum, m) => sum + (parseFloat(m.price) || 0), 0)
    return (itemPrice + modifiersPrice) * quantity
  }

  const handleAddToCart = () => {
    onAddToCart(item, selectedModifiers, quantity)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="relative">
          {item.image_url && (
            <img
              src={item.image_url}
              alt={item.name}
              className="w-full h-64 object-cover"
            />
          )}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">{item.name}</h2>
              <div className="flex flex-wrap gap-2 mb-2">
                {item.is_vegetarian && (
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Vegetarian
                  </Badge>
                )}
                {item.is_vegan && (
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Vegan
                  </Badge>
                )}
                {item.is_spicy && (
                  <Badge variant="outline" className="bg-red-50 text-red-700">
                    Spicy
                  </Badge>
                )}
                {item.is_low_stock && (
                  <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                    Low Stock
                  </Badge>
                )}
                {!item.is_available && (
                  <Badge variant="outline" className="bg-red-50 text-red-700">
                    Sold Out
                  </Badge>
                )}
              </div>
              <p className="text-gray-600">{item.description}</p>
            </div>
            <div className="text-2xl font-bold ml-4">
              {formatCurrency(item.price, 'INR')}
            </div>
          </div>

          {/* Nutrition Info */}
          <NutritionInfo
            calories={item.calories}
            macros={item.macros}
            allergens={item.allergens}
          />

          {/* Modifiers */}
          {item.modifiers && item.modifiers.length > 0 && (
            <div className="mb-4">
              <h3 className="font-semibold mb-3">Customize</h3>
              <div className="space-y-6">
                {Object.entries(groupedModifiers).map(([groupKey, modifiers]: [string, any]) => (
                  <div key={groupKey}>
                    <label className="block font-medium mb-2 capitalize">
                      {groupKey.replace('_', ' ')}
                      {modifiers.some((m: any) => m.is_required) && <span className="text-red-500"> *</span>}
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {modifiers.map((modifier: any) => {
                        const isSelected = selectedModifiers.find(m => m.id === modifier.id)
                        const isGroupSelected = modifier.group && selectedModifiers.find(m => m.group === modifier.group && m.id !== modifier.id)
                        
                        return (
                          <button
                            key={modifier.id}
                            onClick={() => handleModifierToggle(modifier)}
                            disabled={!modifier.is_available}
                            className={`p-3 border rounded-lg text-left transition-all ${
                              isSelected
                                ? 'border-primary-600 bg-primary-50 ring-2 ring-primary-200'
                                : isGroupSelected
                                ? 'border-gray-300 bg-gray-50'
                                : 'border-gray-300 hover:border-primary-300'
                            } ${!modifier.is_available ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{modifier.name}</span>
                              {modifier.price > 0 && (
                                <span className="text-sm text-gray-600">
                                  +{formatCurrency(modifier.price, 'INR')}
                                </span>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Special Instructions */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Special Instructions (Optional)
            </label>
            <textarea
              value={specialInstructions}
              onChange={(e) => setSpecialInstructions(e.target.value)}
              placeholder="Any special requests?"
              className="w-full p-3 border rounded-lg"
              rows={3}
            />
          </div>

          {/* Quantity */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-10 h-10 border rounded-lg flex items-center justify-center"
              >
                -
              </button>
              <span className="font-semibold w-12 text-center">{quantity}</span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="w-10 h-10 border rounded-lg flex items-center justify-center"
              >
                +
              </button>
            </div>
          </div>

          {/* Total */}
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="font-semibold">Total</span>
              <span className="text-2xl font-bold">{formatCurrency(calculateTotal(), 'INR')}</span>
            </div>
          </div>

          {/* Add to Cart Button */}
          <Button
            onClick={handleAddToCart}
            disabled={!item.is_available}
            className="w-full"
            size="lg"
          >
            <ShoppingCart className="w-5 h-5 mr-2" />
            Add to Cart - {formatCurrency(calculateTotal(), 'INR')}
          </Button>
        </div>
      </div>
    </div>
  )
}

