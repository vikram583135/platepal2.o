import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AdminLayout from './components/Layout/AdminLayout'
import LoginPage from './pages/Auth/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UsersPage from './pages/Users/UsersPage'
import UserDetailPage from './pages/Users/UserDetailPage'
import OrdersPage from './pages/Orders/OrdersPage'
import APITokensPage from './pages/Settings/APITokensPage'
import TransactionsPage from './pages/Financials/TransactionsPage'
import ExecutiveDashboardPage from './pages/Analytics/ExecutiveDashboardPage'
import ReviewsModerationPage from './pages/Moderation/ReviewsModerationPage'
import RestaurantContentPage from './pages/Content/RestaurantContentPage'
import CampaignsPage from './pages/Marketplace/CampaignsPage'
import CatalogPage from './pages/Marketplace/CatalogPage'
import HealthDashboardPage from './pages/System/HealthDashboardPage'
import IncidentsPage from './pages/System/IncidentsPage'
import AuditLogsPage from './pages/Security/AuditLogsPage'
import GDPRPage from './pages/Security/GDPRPage'
import RulesPage from './pages/Automation/RulesPage'
import WebhooksPage from './pages/Automation/WebhooksPage'
import IntegrationsPage from './pages/Integrations/IntegrationsPage'
import APIExplorerPage from './pages/Integrations/APIExplorerPage'
import FraudDashboardPage from './pages/Fraud/FraudDashboardPage'
import ChargebacksPage from './pages/Financials/ChargebacksPage'
import FeatureFlagsPage from './pages/FeatureFlags/FeatureFlagsPage'
import SupportConsolePage from './pages/Support/SupportConsolePage'
import RestaurantsPage from './pages/Restaurants/RestaurantsPage'
import DeliveryPartnersPage from './pages/Delivery/DeliveryPartnersPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <AdminLayout>{children}</AdminLayout>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users/:id"
          element={
            <ProtectedRoute>
              <UserDetailPage />
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
          path="/settings/api-tokens"
          element={
            <ProtectedRoute>
              <APITokensPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/financials/transactions"
          element={
            <ProtectedRoute>
              <TransactionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics/executive"
          element={
            <ProtectedRoute>
              <ExecutiveDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/moderation/reviews"
          element={
            <ProtectedRoute>
              <ReviewsModerationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/content/restaurants"
          element={
            <ProtectedRoute>
              <RestaurantContentPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/marketplace/campaigns"
          element={
            <ProtectedRoute>
              <CampaignsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/marketplace/catalog"
          element={
            <ProtectedRoute>
              <CatalogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/system/health"
          element={
            <ProtectedRoute>
              <HealthDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/system/incidents"
          element={
            <ProtectedRoute>
              <IncidentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/security/audit-logs"
          element={
            <ProtectedRoute>
              <AuditLogsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/security/gdpr"
          element={
            <ProtectedRoute>
              <GDPRPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/automation/rules"
          element={
            <ProtectedRoute>
              <RulesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/automation/webhooks"
          element={
            <ProtectedRoute>
              <WebhooksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/integrations"
          element={
            <ProtectedRoute>
              <IntegrationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/integrations/api-explorer"
          element={
            <ProtectedRoute>
              <APIExplorerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/fraud"
          element={
            <ProtectedRoute>
              <FraudDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/financials/chargebacks"
          element={
            <ProtectedRoute>
              <ChargebacksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feature-flags"
          element={
            <ProtectedRoute>
              <FeatureFlagsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/support"
          element={
            <ProtectedRoute>
              <SupportConsolePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/restaurants"
          element={
            <ProtectedRoute>
              <RestaurantsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/delivery"
          element={
            <ProtectedRoute>
              <DeliveryPartnersPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

