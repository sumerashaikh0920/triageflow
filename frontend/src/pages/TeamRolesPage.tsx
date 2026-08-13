import { Check, X } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { mockTeam, permissionMatrix } from '@/lib/mock-data'

const roleLabels: Record<string, string> = { agent: 'Agent', team_lead: 'Team Lead', admin: 'Admin' }
const roleVariant: Record<string, 'info' | 'default' | 'success'> = { agent: 'info', team_lead: 'default', admin: 'success' }

export function TeamRolesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Team &amp; Roles</h1>
        <p className="text-sm text-muted-foreground">Team workload and role-based permissions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>Current workload and status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2 font-medium">Member</th>
                  <th className="px-3 py-2 font-medium">Role</th>
                  <th className="px-3 py-2 font-medium">Active tickets</th>
                  <th className="px-3 py-2 font-medium">Resolved today</th>
                  <th className="px-3 py-2 font-medium">Avg handle time</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {mockTeam.map(member => (
                  <tr key={member.id} className="border-b border-border last:border-0">
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Avatar initials={member.avatar} size="sm" status={member.status} />
                        <div>
                          <p className="text-sm font-medium text-foreground">{member.name}</p>
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2"><Badge variant={roleVariant[member.role]}>{roleLabels[member.role]}</Badge></td>
                    <td className="px-3 py-2 tabular-nums">{member.activeTickets}</td>
                    <td className="px-3 py-2 tabular-nums">{member.resolvedToday}</td>
                    <td className="px-3 py-2 tabular-nums">{member.avgHandleTime}</td>
                    <td className="px-3 py-2 capitalize text-xs text-muted-foreground">{member.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Roles &amp; Permissions</CardTitle>
          <CardDescription>What each role can do in TriageFlow</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2 font-medium">Action</th>
                  <th className="px-3 py-2 font-medium text-center">Agent</th>
                  <th className="px-3 py-2 font-medium text-center">Team Lead</th>
                  <th className="px-3 py-2 font-medium text-center">Admin</th>
                </tr>
              </thead>
              <tbody>
                {permissionMatrix.map(row => (
                  <tr key={row.action} className="border-b border-border last:border-0">
                    <td className="px-3 py-2 text-foreground">{row.action}</td>
                    <td className="px-3 py-2 text-center">
                      {row.agent ? <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 inline" /> : <X className="w-4 h-4 text-muted-foreground/40 inline" />}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {row.team_lead ? <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 inline" /> : <X className="w-4 h-4 text-muted-foreground/40 inline" />}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {row.admin ? <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 inline" /> : <X className="w-4 h-4 text-muted-foreground/40 inline" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
