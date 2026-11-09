import { createContext } from 'react'
import { UserRole } from '@/lib/mock-data'

export interface AuthUser {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
}

export interface AuthContextValue {
  user: AuthUser | null
  login: (role: UserRole) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
