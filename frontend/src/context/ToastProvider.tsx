import { useCallback, useRef, useState, ReactNode } from 'react'
import { ToastContext, ToastItem } from './toast-context'

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
