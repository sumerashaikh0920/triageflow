import { createContext, useCallback, useContext, useRef, useState, ReactNode } from 'react'

export interface ToastItem {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'success' | 'error'
}

interface ToastContextValue {
  toasts: ToastItem[]
  showToast: (toast: Omit<ToastItem, 'id'>) => void
  dismissToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const counter = useRef(0)

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const showToast = useCallback((toast: Omit<ToastItem, 'id'>) => {
    counter.current += 1
    const id = `toast-${counter.current}-${Date.now()}`
    setToasts(prev => [...prev, { ...toast, id }])
    setTimeout(() => dismissToast(id), 4000)
  }, [dismissToast])

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
