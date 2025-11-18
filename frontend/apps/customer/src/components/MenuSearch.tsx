import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { Input } from '@/packages/ui/components/input'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'

interface MenuSearchProps {
  restaurantId: string
  onItemSelect?: (item: any) => void
}

export default function MenuSearch({ restaurantId, onItemSelect }: MenuSearchProps) {
  const [query, setQuery] = useState('')
  const [showResults, setShowResults] = useState(false)

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['menu-search', restaurantId, query],
    queryFn: async () => {
      const response = await apiClient.get(`/restaurants/restaurants/${restaurantId}/menu_search/?q=${encodeURIComponent(query)}`)
      return response.data.items || []
    },
    enabled: query.length >= 2 && showResults,
  })

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <Input
          type="text"
          placeholder="Search menu items..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            if (e.target.value.length >= 2) {
              setShowResults(true)
            }
          }}
          onFocus={() => query.length >= 2 && setShowResults(true)}
          className="pl-10 pr-10"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('')
              setShowResults(false)
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
      </div>

      {showResults && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Searching...</div>
          ) : searchResults && searchResults.length > 0 ? (
            <div className="p-2">
              {searchResults.map((item: any) => (
                <button
                  key={item.id}
                  onClick={() => {
                    if (onItemSelect) {
                      onItemSelect(item)
                    }
                    setShowResults(false)
                    setQuery('')
                  }}
                  className="w-full text-left p-3 hover:bg-gray-50 rounded flex items-center gap-3"
                >
                  {item.image_url && (
                    <img src={item.image_url} alt={item.name} className="w-12 h-12 object-cover rounded" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium">{item.name}</div>
                    <div className="text-sm text-gray-600">{item.category_name}</div>
                  </div>
                  <div className="font-semibold">₹{item.price}</div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500">No items found</div>
          )}
        </div>
      )}
    </div>
  )
}

