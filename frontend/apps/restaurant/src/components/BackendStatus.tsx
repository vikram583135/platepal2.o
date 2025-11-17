import { useEffect, useState } from 'react'
import apiClient from '@/packages/api/client'
import { AlertCircle } from 'lucide-react'

export function BackendStatus() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const [apiUrl, setApiUrl] = useState<string>('')

  useEffect(() => {
    const checkBackend = async () => {
      const url = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
      setApiUrl(url)
      
      try {
        // Try to hit any endpoint - if we get a response (even 404/401), server is running
        await apiClient.get('/restaurants/restaurants/', { timeout: 3000 })
        setIsOnline(true)
      } catch (error: any) {
        // If we get any HTTP response, the server is running
        // Only mark as offline if there's no response at all (network error)
        if (error.response) {
          setIsOnline(true) // Server is running, just got an error response
        } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK' || error.message?.includes('timeout')) {
          setIsOnline(false) // Server is not reachable
        } else {
          setIsOnline(true) // Assume online if we can't determine
        }
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (isOnline === null || isOnline) {
    return null
  }

  return (
    <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
      <div className="flex items-center">
        <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-red-800">Backend Server Not Running</p>
          <p className="text-sm text-red-700 mt-1">
            Cannot connect to backend at <code className="bg-red-100 px-1 rounded">{apiUrl}</code>
          </p>
          <p className="text-xs text-red-600 mt-2">
            To start the backend server, run: <code className="bg-red-100 px-1 rounded">cd backend && python manage.py runserver</code>
          </p>
        </div>
      </div>
    </div>
  )
}

