import { useNavigate } from 'react-router-dom'
import { Zap, Headset, ShieldCheck, Crown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { useAuth } from '@/context/AuthContext'
import type { UserRole } from '@/lib/mock-data'

const roleOptions: { role: UserRole; title: string; description: string; icon: typeof Headset }[] = [
  { role: 'agent', title: 'Agent', description: 'Handle assigned tickets and respond to customers', icon: Headset },
  { role: 'team_lead', title: 'Team Lead', description: 'Oversee team queues, routing, and feedback review', icon: ShieldCheck },
  { role: 'admin', title: 'Admin', description: 'Full access: integrations, retraining, team management', icon: Crown },
]

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleLogin = (role: UserRole) => {
    login(role)
    navigate('/', { replace: true })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-500 flex items-center justify-center mb-4">
            <Zap className="w-6 h-6 text-white" fill="white" />
          </div>
          <h1 className="text-xl font-bold text-foreground">TriageFlow</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-powered support ticket triage</p>
        </div>

        <Card>
          <CardContent className="pt-5">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Demo login &mdash; choose a role
            </p>
            <div className="space-y-2" role="list" aria-label="Demo login role options">
              {roleOptions.map(opt => (
                <button
                  key={opt.role}
                  role="listitem"
                  onClick={() => handleLogin(opt.role)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg border border-border text-left hover:border-brand-400 hover:bg-brand-50/50 dark:hover:bg-brand-900/10 transition-colors"
                >
                  <div className="w-9 h-9 rounded-lg bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center flex-shrink-0">
                    <opt.icon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground">{opt.title}</p>
                    <p className="text-xs text-muted-foreground">{opt.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          This is a portfolio demo. No real credentials required &mdash; pick a role to explore the dashboard.
        </p>
      </div>
    </div>
  )
}
