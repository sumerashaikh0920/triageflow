import { Moon, Sun, User, Zap } from 'lucide-react'
import * as SwitchPrimitive from '@radix-ui/react-switch'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Avatar } from '@/components/ui/Avatar'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { cn } from '@/lib/utils'

export function SettingsPage() {
  const { user } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-lg font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground">Preferences for this demo session</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Signed in via demo login</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <Avatar initials={user?.avatar ?? '?'} size="lg" />
            <div>
              <p className="text-sm font-semibold text-foreground flex items-center gap-1.5"><User className="w-3.5 h-3.5" />{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Toggle between light and dark mode</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-foreground">
              {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              Dark mode
            </div>
            <SwitchPrimitive.Root
              checked={theme === 'dark'}
              onCheckedChange={toggleTheme}
              className={cn(
                'w-10 h-6 rounded-full relative transition-colors data-[state=checked]:bg-brand-500 bg-muted',
              )}
              aria-label="Toggle dark mode"
            >
              <SwitchPrimitive.Thumb className="block w-4 h-4 rounded-full bg-white shadow translate-x-1 transition-transform data-[state=checked]:translate-x-5" />
            </SwitchPrimitive.Root>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" />About this demo</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            This dashboard runs entirely on local mock data and browser state for portfolio/demo purposes. No data
            is sent to a real backend from this screen.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
