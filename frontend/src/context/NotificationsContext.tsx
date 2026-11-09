import { useContext } from 'react'
import { NotificationsContext } from './notifications-context'

// The provider lives in NotificationsProvider.tsx so that component files only export components
// (required by react-refresh/only-export-components for Fast Refresh).
export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider')
  return ctx
}
