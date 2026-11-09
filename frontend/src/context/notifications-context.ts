import { createContext } from 'react'
import { NotificationItem } from '@/lib/mock-data'

export interface NotificationsContextValue {
  notifications: NotificationItem[]
  unreadCount: number
  markAllRead: () => void
  markRead: (id: string) => void
}

export const NotificationsContext = createContext<NotificationsContextValue | null>(null)
