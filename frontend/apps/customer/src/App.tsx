import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import OfflineBanner from './components/OfflineBanner'
import HomePage from './pages/HomePage'
import RestaurantsPage from './pages/RestaurantsPage'
import RestaurantDetailPage from './pages/RestaurantDetailPage'
import CartPage from './pages/CartPage'
import CheckoutPage from './pages/CheckoutPage'
import OrdersPage from './pages/OrdersPage'
import OrderDetailPage from './pages/OrderDetailPage'
import OrderTrackingPage from './pages/OrderTrackingPage'
import ProfilePage from './pages/ProfilePage'
import SettingsPage from './pages/SettingsPage'
import OffersPage from './pages/OffersPage'
import WalletPage from './pages/WalletPage'
import NotificationsPage from './pages/NotificationsPage'
import SupportPage from './pages/SupportPage'
import TicketDetailPage from './pages/TicketDetailPage'
import MembershipPage from './pages/MembershipPage'
import RewardsPage from './pages/RewardsPage'
import SubscriptionPage from './pages/SubscriptionPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import OTPVerificationPage from './pages/OTPVerificationPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <OfflineBanner />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/verify-otp" element={<OTPVerificationPage />} />

        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/restaurants" element={<RestaurantsPage />} />
          <Route path="/restaurants/:id" element={<RestaurantDetailPage />} />
          <Route path="/cart" element={<CartPage />} />

          <Route
            path="/checkout"
            element={
              <ProtectedRoute>
                <CheckoutPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/orders"
            element={
              <ProtectedRoute>
                <OrdersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/orders/:id"
            element={
              <ProtectedRoute>
                <OrderDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/orders/:id/track"
            element={
              <ProtectedRoute>
                <OrderTrackingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/offers"
            element={
              <ProtectedRoute>
                <OffersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/wallet"
            element={
              <ProtectedRoute>
                <WalletPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support"
            element={
              <ProtectedRoute>
                <SupportPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/tickets/:id"
            element={
              <ProtectedRoute>
                <TicketDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/membership"
            element={
              <ProtectedRoute>
                <MembershipPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rewards"
            element={
              <ProtectedRoute>
                <RewardsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/subscription"
            element={
              <ProtectedRoute>
                <SubscriptionPage />
              </ProtectedRoute>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

