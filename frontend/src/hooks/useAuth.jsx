import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center justify-center min-h-screen text-slate-500">Laden...</div>
  if (!user) {
    window.location.href = '/auth/login'
    return null
  }

  return <AuthContext.Provider value={user}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
