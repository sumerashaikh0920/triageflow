import { createContext } from 'react'

export interface ToastItem {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'success' | 'error'
}

export interface ToastContextValue {
  toasts: ToastItem[]
  showToast: (toast: Omit<ToastItem, 'id'>) => void
  dismissToast: (id: string) => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)
