import { createContext, useContext, useState, ReactNode } from 'react'
import { UserRole } from '@/lib/mock-data'

export interface AuthUser {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
}

const DEMO_USERS: Record<UserRole, AuthUser> = {
  agent: {
    id: 'u2',
    name: 'James Park',
    email: 'james@triageflow.io',
    role: 'agent',
    avatar: 'JP',
  },
  team_lead: {
    id: 'u1',
    name: 'Sarah Chen',
    email: 'sarah@triageflow.io',
    role: 'team_lead',
    avatar: 'SC',
  },
  admin: {
    id: 'u5',
    name: 'Priya Nair',
    email: 'priya@triageflow.io',
    role: 'admin',
    avatar: 'PN',
  },
}

interface AuthContextValue {
  user: AuthUser | null
  login: (role: UserRole) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)

  const login = (role: UserRole) => setUser(DEMO_USERS[role])
  const logout = () => setUser(null)

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
