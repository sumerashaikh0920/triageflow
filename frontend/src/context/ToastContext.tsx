import { useContext } from 'react'
import { ToastContext } from './toast-context'

export type { ToastItem } from './toast-context'

// The provider lives in ToastProvider.tsx so that component files only export components
// (required by react-refresh/only-export-components for Fast Refresh).
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
