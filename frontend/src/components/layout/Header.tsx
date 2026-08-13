import { useState } from 'react'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { Search, Bell, Moon, Sun, LogOut, ChevronDown } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { useNotifications } from '@/context/NotificationsContext'
import { cn } from '@/lib/utils'

const roleLabels: Record<string, string> = {
  agent: 'Agent',
  team_lead: 'Team Lead',
  admin: 'Admin',
}

export function Header({ onSearch }: { onSearch?: (query: string) => void }) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { notifications, unreadCount, markAllRead, markRead } = useNotifications()
  const [query, setQuery] = useState('')

  return (
    <header className="h-16 flex items-center gap-4 px-6 border-b border-border bg-card flex-shrink-0">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          value={query}
          onChange={e => {
            setQuery(e.target.value)
            onSearch?.(e.target.value)
          }}
          placeholder="Search tickets, customers, tags..."
          aria-label="Search"
          className="pl-9"
        />
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle dark mode">
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>

        <DropdownMenu.Root onOpenChange={open => open && markAllRead()}>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" aria-label={`${unreadCount} unread notifications`} />
              )}
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              align="end"
              sideOffset={8}
              className="z-50 w-80 rounded-lg border border-border bg-card shadow-lg overflow-hidden"
            >
              <div className="px-4 py-3 border-b border-border">
                <p className="text-sm font-semibold text-foreground">Notifications</p>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-6">You&apos;re all caught up</p>
                ) : (
                  notifications.map(n => (
                    <DropdownMenu.Item
                      key={n.id}
                      onSelect={() => markRead(n.id)}
                      className={cn(
                        'px-4 py-3 border-b border-border last:border-0 cursor-pointer outline-none hover:bg-muted',
                        !n.read && 'bg-brand-50/60 dark:bg-brand-900/10',
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-semibold text-foreground">{n.title}</p>
                        {n.severity === 'critical' && <Badge variant="danger">Critical</Badge>}
                        {n.severity === 'warning' && <Badge variant="warning">Warning</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{n.detail}</p>
                    </DropdownMenu.Item>
                  ))
                )}
              </div>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>

        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-lg hover:bg-muted transition-colors" aria-label="User menu">
              <Avatar initials={user?.avatar ?? '?'} size="sm" />
              <div className="text-left hidden sm:block">
                <p className="text-xs font-semibold text-foreground leading-none">{user?.name}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{user ? roleLabels[user.role] : ''}</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content align="end" sideOffset={8} className="z-50 w-48 rounded-lg border border-border bg-card shadow-lg p-1">
              <DropdownMenu.Item
                onSelect={logout}
                className="flex items-center gap-2 px-3 py-2 text-sm rounded-md cursor-pointer outline-none text-red-600 dark:text-red-400 hover:bg-muted"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign out (demo)
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  )
}
