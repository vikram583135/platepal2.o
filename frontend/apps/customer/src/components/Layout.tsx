import { Outlet } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useCustomerSocket } from '../hooks/useCustomerSocket'
import Navbar from './Navbar'
import Footer from './Footer'

export default function Layout() {
  const { user } = useAuthStore()
  
  // Initialize WebSocket connection for customer
  useCustomerSocket(user?.id)

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

