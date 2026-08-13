import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Inbox,
  Route,
  Timer,
  MessagesSquare,
  LineChart,
  Plug,
  Users,
  Settings,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import type { UserRole } from '@/lib/mock-data'

interface NavItem {
  label: string
  to: string
  icon: typeof LayoutDashboard
  roles?: UserRole[]
}

const navItems: NavItem[] = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Tickets', to: '/tickets', icon: Inbox },
  { label: 'Routing Queue', to: '/routing', icon: Route },
  { label: 'SLA Monitor', to: '/sla', icon: Timer },
  { label: 'Feedback & Retraining', to: '/feedback', icon: MessagesSquare },
  { label: 'Model Metrics', to: '/models', icon: LineChart },
  { label: 'Integrations', to: '/integrations', icon: Plug, roles: ['team_lead', 'admin'] },
  { label: 'Team & Roles', to: '/team', icon: Users, roles: ['team_lead', 'admin'] },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export function Sidebar({ className }: { className?: string }) {
  const { user } = useAuth()

  const visibleItems = navItems.filter(item => !item.roles || (user && item.roles.includes(user.role)))

  return (
    <aside className={cn('w-60 flex-shrink-0 bg-sidebar text-sidebar-foreground flex flex-col', className)}>
      <div className="h-16 flex items-center gap-2 px-5 border-b border-sidebar-border">
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
          <Zap className="w-4 h-4 text-white" fill="white" />
        </div>
        <span className="font-bold text-sm tracking-tight">TriageFlow</span>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1" aria-label="Main navigation">
        {visibleItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-sidebar-accent text-white'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-muted hover:text-sidebar-foreground',
              )
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-sidebar-border text-[11px] text-sidebar-foreground/50">
        TriageFlow v1.0.0 &middot; Demo mode
      </div>
    </aside>
  )
}
