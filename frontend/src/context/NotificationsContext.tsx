import { createContext, useContext, useState, ReactNode } from 'react'
import { initialNotifications, NotificationItem } from '@/lib/mock-data'

interface NotificationsContextValue {
  notifications: NotificationItem[]
  unreadCount: number
  markAllRead: () => void
  markRead: (id: string) => void
}

const NotificationsContext = createContext<NotificationsContextValue | null>(null)

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications)

  const unreadCount = notifications.filter(n => !n.read).length

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  const markRead = (id: string) => setNotifications(prev => prev.map(n => (n.id === id ? { ...n, read: true } : n)))

  return (
    <NotificationsContext.Provider value={{ notifications, unreadCount, markAllRead, markRead }}>
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider')
  return ctx
}
