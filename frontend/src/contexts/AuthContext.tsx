import { createContext, useContext, ReactNode } from 'react'
import { useFrappeAuth } from 'frappe-react-sdk'

interface AuthContextType {
  currentUser: string | null | undefined
  isLoading: boolean
  isValidating: boolean
  isAuthenticated: boolean
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const { currentUser, isLoading, isValidating, logout } = useFrappeAuth()
  
  const value: AuthContextType = {
    currentUser,
    isLoading,
    isValidating,
    isAuthenticated: !!currentUser,
    logout,
  }
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
