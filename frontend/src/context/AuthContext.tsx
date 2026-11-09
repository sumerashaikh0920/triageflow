import { useContext } from 'react'
import { AuthContext } from './auth-context'

export type { AuthUser } from './auth-context'

// The provider lives in AuthProvider.tsx so that component files only export components
// (required by react-refresh/only-export-components for Fast Refresh).
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
