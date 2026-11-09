import { useContext } from 'react'
import { TicketsContext } from './tickets-context'

// The provider lives in TicketsProvider.tsx so that component files only export components
// (required by react-refresh/only-export-components for Fast Refresh).
export function useTickets() {
  const ctx = useContext(TicketsContext)
  if (!ctx) throw new Error('useTickets must be used within TicketsProvider')
  return ctx
}
