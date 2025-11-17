import { useState } from 'react'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { X, Filter } from 'lucide-react'

interface FilterState {
  cuisines: string[]
  minRating: number | null
  maxRating: number | null
  maxDeliveryTime: number | null
  vegOnly: boolean
  pureVeg: boolean
  hasOffers: boolean
  minCost: number | null
  maxCost: number | null
  minHygiene: number | null
  sortBy: string
}

interface RestaurantFiltersProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onClose?: () => void
}

const CUISINES = [
  'Italian', 'Chinese', 'Indian', 'Mexican', 'Japanese',
  'American', 'Thai', 'Mediterranean', 'Fast Food', 'Vegetarian', 'Vegan'
]

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: '-rating', label: 'High Rating' },
  { value: 'delivery_time_minutes', label: 'Fast Delivery' },
  { value: 'cost_for_two', label: 'Cost: Low to High' },
  { value: '-cost_for_two', label: 'Cost: High to Low' },
]

export default function RestaurantFilters({ filters, onFiltersChange, onClose }: RestaurantFiltersProps) {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters)

  const handleCuisineToggle = (cuisine: string) => {
    const newCuisines = localFilters.cuisines.includes(cuisine)
      ? localFilters.cuisines.filter(c => c !== cuisine)
      : [...localFilters.cuisines, cuisine]
    setLocalFilters({ ...localFilters, cuisines: newCuisines })
  }

  const handleApply = () => {
    onFiltersChange(localFilters)
    if (onClose) onClose()
  }

  const handleReset = () => {
    const resetFilters: FilterState = {
      cuisines: [],
      minRating: null,
      maxRating: null,
      maxDeliveryTime: null,
      vegOnly: false,
      pureVeg: false,
      hasOffers: false,
      minCost: null,
      maxCost: null,
      minHygiene: null,
      sortBy: 'relevance',
    }
    setLocalFilters(resetFilters)
    onFiltersChange(resetFilters)
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters & Sort
          </CardTitle>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6 overflow-y-auto max-h-[calc(100vh-200px)]">
        {/* Sort */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
          <select
            value={localFilters.sortBy}
            onChange={(e) => setLocalFilters({ ...localFilters, sortBy: e.target.value })}
            className="w-full p-2 border rounded-lg"
          >
            {SORT_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Cuisines */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Cuisines</label>
          <div className="flex flex-wrap gap-2">
            {CUISINES.map(cuisine => (
              <button
                key={cuisine}
                onClick={() => handleCuisineToggle(cuisine)}
                className={`px-3 py-1 rounded-full text-sm border ${
                  localFilters.cuisines.includes(cuisine)
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary-300'
                }`}
              >
                {cuisine}
              </button>
            ))}
          </div>
        </div>

        {/* Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Rating</label>
          <div className="flex gap-2">
            <input
              type="number"
              min="0"
              max="5"
              step="0.1"
              placeholder="Min"
              value={localFilters.minRating || ''}
              onChange={(e) => setLocalFilters({ ...localFilters, minRating: e.target.value ? parseFloat(e.target.value) : null })}
              className="flex-1 p-2 border rounded-lg"
            />
            <span className="self-center">to</span>
            <input
              type="number"
              min="0"
              max="5"
              step="0.1"
              placeholder="Max"
              value={localFilters.maxRating || ''}
              onChange={(e) => setLocalFilters({ ...localFilters, maxRating: e.target.value ? parseFloat(e.target.value) : null })}
              className="flex-1 p-2 border rounded-lg"
            />
          </div>
        </div>

        {/* Delivery Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Max Delivery Time (minutes)</label>
          <input
            type="number"
            min="0"
            placeholder="e.g., 30"
            value={localFilters.maxDeliveryTime || ''}
            onChange={(e) => setLocalFilters({ ...localFilters, maxDeliveryTime: e.target.value ? parseInt(e.target.value) : null })}
            className="w-full p-2 border rounded-lg"
          />
        </div>

        {/* Cost for Two */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Cost for Two</label>
          <div className="flex gap-2">
            <input
              type="number"
              min="0"
              placeholder="Min"
              value={localFilters.minCost || ''}
              onChange={(e) => setLocalFilters({ ...localFilters, minCost: e.target.value ? parseFloat(e.target.value) : null })}
              className="flex-1 p-2 border rounded-lg"
            />
            <span className="self-center">to</span>
            <input
              type="number"
              min="0"
              placeholder="Max"
              value={localFilters.maxCost || ''}
              onChange={(e) => setLocalFilters({ ...localFilters, maxCost: e.target.value ? parseFloat(e.target.value) : null })}
              className="flex-1 p-2 border rounded-lg"
            />
          </div>
        </div>

        {/* Hygiene Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Min Hygiene Rating</label>
          <input
            type="number"
            min="0"
            max="5"
            step="0.1"
            placeholder="e.g., 4.0"
            value={localFilters.minHygiene || ''}
            onChange={(e) => setLocalFilters({ ...localFilters, minHygiene: e.target.value ? parseFloat(e.target.value) : null })}
            className="w-full p-2 border rounded-lg"
          />
        </div>

        {/* Toggles */}
        <div className="space-y-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={localFilters.vegOnly}
              onChange={(e) => setLocalFilters({ ...localFilters, vegOnly: e.target.checked })}
              className="w-4 h-4"
            />
            <span className="text-sm">Veg Only</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={localFilters.pureVeg}
              onChange={(e) => setLocalFilters({ ...localFilters, pureVeg: e.target.checked })}
              className="w-4 h-4"
            />
            <span className="text-sm">Pure Veg</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={localFilters.hasOffers}
              onChange={(e) => setLocalFilters({ ...localFilters, hasOffers: e.target.checked })}
              className="w-4 h-4"
            />
            <span className="text-sm">Has Offers</span>
          </label>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t">
          <Button onClick={handleApply} className="flex-1">Apply Filters</Button>
          <Button variant="outline" onClick={handleReset}>Reset</Button>
        </div>
      </CardContent>
    </Card>
  )
}

