import { useContext } from 'react'
import { ThemeContext } from './theme-context'

// The provider lives in ThemeProvider.tsx so that component files only export components
// (required by react-refresh/only-export-components for Fast Refresh).
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
