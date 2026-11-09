import { useState, ReactNode } from 'react'
import { UserRole } from '@/lib/mock-data'
import { AuthContext, AuthUser } from './auth-context'

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
