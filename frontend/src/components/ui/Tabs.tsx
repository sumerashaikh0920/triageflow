import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cn } from '@/lib/utils'
import { ReactNode } from 'react'

export const Tabs = TabsPrimitive.Root

export function TabsList({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <TabsPrimitive.List
      className={cn('inline-flex items-center gap-1 rounded-lg bg-muted p-1', className)}
    >
      {children}
    </TabsPrimitive.List>
  )
}

export function TabsTrigger({ value, children }: { value: string; children: ReactNode }) {
  return (
    <TabsPrimitive.Trigger
      value={value}
      className="px-3 py-1.5 text-xs font-medium rounded-md text-muted-foreground transition-colors data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm"
    >
      {children}
    </TabsPrimitive.Trigger>
  )
}

export function TabsContent({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  return (
    <TabsPrimitive.Content value={value} className={cn('mt-4 focus:outline-none', className)}>
      {children}
    </TabsPrimitive.Content>
  )
}
