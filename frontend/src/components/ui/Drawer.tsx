import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export const Drawer = DialogPrimitive.Root
export const DrawerTrigger = DialogPrimitive.Trigger

export function DrawerContent({
  children,
  title,
  className,
}: {
  children: ReactNode
  title: string
  className?: string
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/40 data-[state=open]:animate-in data-[state=open]:fade-in" />
      <DialogPrimitive.Content
        className={cn(
          'fixed right-0 top-0 z-50 h-full w-full max-w-xl bg-card border-l border-border shadow-2xl overflow-y-auto',
          'data-[state=open]:animate-in data-[state=open]:slide-in-from-right',
          className,
        )}
        aria-describedby={undefined}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-border bg-card">
          <DialogPrimitive.Title className="text-sm font-semibold text-foreground">{title}</DialogPrimitive.Title>
          <DialogPrimitive.Close
            aria-label="Close"
            className="p-1.5 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </DialogPrimitive.Close>
        </div>
        <div className="p-5">{children}</div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  )
}
