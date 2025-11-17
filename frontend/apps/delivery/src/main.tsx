import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
})

// Keyboard shortcuts handler
document.addEventListener('keydown', (e) => {
  // Alt + S for settings
  if (e.altKey && e.key === 's') {
    e.preventDefault()
    window.location.href = '/settings'
  }
  // Alt + D for dashboard
  if (e.altKey && e.key === 'd') {
    e.preventDefault()
    window.location.href = '/'
  }
  // Alt + O for offers
  if (e.altKey && e.key === 'o') {
    e.preventDefault()
    window.location.href = '/offers'
  }
  // Alt + E for earnings
  if (e.altKey && e.key === 'e') {
    e.preventDefault()
    window.location.href = '/earnings'
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)

