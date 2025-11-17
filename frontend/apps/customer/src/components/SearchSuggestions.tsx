import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Search, Clock, TrendingUp, Mic } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface SearchSuggestionsProps {
  query: string
  onSelect: (query: string) => void
  onVoiceSearch?: () => void
}

export default function SearchSuggestions({ query, onSelect, onVoiceSearch }: SearchSuggestionsProps) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const { isAuthenticated } = useAuthStore()
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: suggestions } = useQuery({
    queryKey: ['search-suggestions', query],
    queryFn: async () => {
      if (!query || query.length < 2) return { suggestions: [] }
      const response = await apiClient.get(`/restaurants/search/suggestions/?q=${encodeURIComponent(query)}`)
      return response.data
    },
    enabled: query.length >= 2,
  })

  const { data: recentSearches } = useQuery({
    queryKey: ['recent-searches'],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/search/recent/')
      return response.data
    },
    enabled: isAuthenticated && !query,
  })

  const { data: popularSearches } = useQuery({
    queryKey: ['popular-searches'],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/search/popular/')
      return response.data
    },
    enabled: !query,
  })

  useEffect(() => {
    setShowSuggestions(query.length > 0 || (recentSearches?.searches?.length > 0) || (popularSearches?.searches?.length > 0))
  }, [query, recentSearches, popularSearches])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleVoiceSearch = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-US'

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        onSelect(transcript)
      }

      recognition.onerror = () => {
        alert('Voice recognition failed. Please try again.')
      }

      recognition.start()
    } else {
      alert('Voice search is not supported in your browser')
    }
  }

  if (!showSuggestions) return null

  return (
    <div ref={containerRef} className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
      {query.length >= 2 && suggestions?.suggestions && suggestions.suggestions.length > 0 && (
        <div className="p-2">
          <div className="text-xs font-semibold text-gray-500 px-2 py-1">Suggestions</div>
          {suggestions.suggestions.map((suggestion: any, index: number) => (
            <button
              key={index}
              onClick={() => {
                onSelect(suggestion.text)
                setShowSuggestions(false)
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded flex items-center gap-2"
            >
              <Search className="w-4 h-4 text-gray-400" />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{suggestion.text}</div>
                {suggestion.restaurant && (
                  <div className="text-xs text-gray-500">{suggestion.restaurant}</div>
                )}
                {suggestion.type && (
                  <span className="text-xs text-gray-400 capitalize">{suggestion.type}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {!query && recentSearches?.searches && recentSearches.searches.length > 0 && (
        <div className="p-2 border-t">
          <div className="text-xs font-semibold text-gray-500 px-2 py-1 flex items-center gap-2">
            <Clock className="w-3 h-3" />
            Recent Searches
          </div>
          {recentSearches.searches.map((search: any, index: number) => (
            <button
              key={index}
              onClick={() => {
                onSelect(search.query)
                setShowSuggestions(false)
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded"
            >
              {search.query}
            </button>
          ))}
        </div>
      )}

      {!query && popularSearches?.searches && popularSearches.searches.length > 0 && (
        <div className="p-2 border-t">
          <div className="text-xs font-semibold text-gray-500 px-2 py-1 flex items-center gap-2">
            <TrendingUp className="w-3 h-3" />
            Popular Searches
          </div>
          {popularSearches.searches.map((search: any, index: number) => (
            <button
              key={index}
              onClick={() => {
                onSelect(search.query)
                setShowSuggestions(false)
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded flex justify-between"
            >
              <span>{search.query}</span>
              <span className="text-xs text-gray-400">{search.count} searches</span>
            </button>
          ))}
        </div>
      )}

      {onVoiceSearch && (
        <div className="p-2 border-t">
          <button
            onClick={handleVoiceSearch}
            className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded flex items-center gap-2"
          >
            <Mic className="w-4 h-4 text-gray-400" />
            <span>Voice Search</span>
          </button>
        </div>
      )}
    </div>
  )
}

