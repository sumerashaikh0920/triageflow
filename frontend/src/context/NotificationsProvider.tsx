import { useState, ReactNode } from 'react'
import { initialNotifications, NotificationItem } from '@/lib/mock-data'
import { NotificationsContext } from './notifications-context'

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
