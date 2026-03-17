import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { FrappeProvider } from 'frappe-react-sdk'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'
import Items from './pages/Items'
import ItemDetail from './pages/ItemDetail'
import ActivateQR from './pages/ActivateQR'
import Recovery from './pages/Recovery'
import RecoveryDetail from './pages/RecoveryDetail'
import NotificationSettings from './pages/NotificationSettings'

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    window.location.href = '/login'
    return null
  }
  
  return <>{children}</>
}

const AppRoutes = () => {
  const { isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }
  
  return (
    <Routes>
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />
      <Route
        path="/items"
        element={
          <ProtectedRoute>
            <Items />
          </ProtectedRoute>
        }
      />
      <Route
        path="/items/:id"
        element={
          <ProtectedRoute>
            <ItemDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/activate-qr"
        element={
          <ProtectedRoute>
            <ActivateQR />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recovery"
        element={
          <ProtectedRoute>
            <Recovery />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recovery/:id"
        element={
          <ProtectedRoute>
            <RecoveryDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings/notifications"
        element={
          <ProtectedRoute>
            <NotificationSettings />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  // Use empty string for same-origin requests (FrappeProvider defaults to current origin)
  // Only use VITE_FRAPPE_URL if it's a valid non-empty absolute URL
  const frappeUrl = (typeof import.meta.env.VITE_FRAPPE_URL === 'string' && 
                     import.meta.env.VITE_FRAPPE_URL && 
                     import.meta.env.VITE_FRAPPE_URL !== '/')
    ? import.meta.env.VITE_FRAPPE_URL 
    : ''
  
  return (
    <FrappeProvider
      url={frappeUrl}
      socketPort={import.meta.env.DEV ? '9000' : undefined}
    >
      <AuthProvider>
        <BrowserRouter basename="/frontend">
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </FrappeProvider>
  )
}

export default App
