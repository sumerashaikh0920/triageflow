// ─── Types ─────────────────────────────────────────────────────────────────

export type TicketPriority = 'critical' | 'high' | 'medium' | 'low'
export type TicketStatus   = 'open' | 'in_progress' | 'pending' | 'resolved' | 'closed'
export type TicketCategory = 'billing' | 'technical' | 'account' | 'general' | 'shipping'
export type TicketSentiment = 'positive' | 'neutral' | 'negative' | 'frustrated'
export type UserRole       = 'agent' | 'team_lead' | 'admin'

export interface TicketMessage {
  id: string
  author: string
  role: 'customer' | 'agent' | 'system'
  body: string
  timestamp: string
}

export interface ActivityEvent {
  id: string
  type: 'created' | 'assigned' | 'status_change' | 'category_correction' | 'urgency_change' | 'ai_prediction' | 'ai_accepted' | 'comment' | 'resolved'
  actor: string
  detail: string
  timestamp: string
}

export interface Ticket {
  id: string
  subject: string
  customer: string
  customerEmail: string
  customerCompany: string
  priority: TicketPriority
  status: TicketStatus
  category: TicketCategory
  sentiment: TicketSentiment
  assignee: string | null
  aiConfidence: number
  aiSuggestedCategory: TicketCategory
  aiSuggestedRouting: string
  aiPredictionAccepted: boolean | null
  createdAt: string
  updatedAt: string
  slaDeadline: string
  slaBreached: boolean
  tags: string[]
  messages: TicketMessage[]
  activity: ActivityEvent[]
}

export interface TeamMember {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
  activeTickets: number
  resolvedToday: number
  avgHandleTime: string
  status: 'online' | 'away' | 'offline'
}

export interface MetricPoint { date: string; value: number }

// ─── Tickets ────────────────────────────────────────────────────────────────

function baseMessages(customer: string, subject: string): TicketMessage[] {
  return [
    { id: 'm1', author: customer, role: 'customer', body: subject, timestamp: '2026-08-11T08:14:00Z' },
    { id: 'm2', author: 'TriageFlow Bot', role: 'system', body: 'Ticket received and routed for triage.', timestamp: '2026-08-11T08:14:05Z' },
  ]
}

function baseActivity(actor: string): ActivityEvent[] {
  return [
    { id: 'a1', type: 'created', actor: 'System', detail: 'Ticket created from inbound email', timestamp: '2026-08-11T08:14:00Z' },
    { id: 'a2', type: 'ai_prediction', actor: 'AI Classifier', detail: 'Predicted category and routing suggestion generated', timestamp: '2026-08-11T08:14:06Z' },
    { id: 'a3', type: 'assigned', actor: 'Router', detail: `Assigned to ${actor}`, timestamp: '2026-08-11T08:20:00Z' },
  ]
}

export const mockTickets: Ticket[] = [
  { id: 'TKT-1042', subject: 'Cannot access my account after password reset', customer: 'Alice Johnson', customerEmail: 'alice@acme.com', customerCompany: 'Acme Corp', priority: 'critical', status: 'open', category: 'account', sentiment: 'frustrated', assignee: 'Sarah Chen', aiConfidence: 0.94, aiSuggestedCategory: 'account', aiSuggestedRouting: 'Account & Access Team', aiPredictionAccepted: null, createdAt: '2026-08-11T08:14:00Z', updatedAt: '2026-08-11T09:02:00Z', slaDeadline: '2026-08-11T12:14:00Z', slaBreached: false, tags: ['password', 'auth'], messages: baseMessages('Alice Johnson', 'Cannot access my account after password reset — this is urgent, I need this fixed today.'), activity: baseActivity('Sarah Chen') },
  { id: 'TKT-1041', subject: 'Double charged on last invoice #INV-8821', customer: 'Bob Martinez', customerEmail: 'bob@startup.io', customerCompany: 'Startup.io', priority: 'high', status: 'in_progress', category: 'billing', sentiment: 'negative', assignee: 'James Park', aiConfidence: 0.88, aiSuggestedCategory: 'billing', aiSuggestedRouting: 'Billing Team', aiPredictionAccepted: true, createdAt: '2026-08-11T07:55:00Z', updatedAt: '2026-08-11T08:40:00Z', slaDeadline: '2026-08-11T15:55:00Z', slaBreached: false, tags: ['billing', 'refund'], messages: baseMessages('Bob Martinez', 'I was charged twice for invoice INV-8821, please refund the duplicate charge.'), activity: baseActivity('James Park') },
  { id: 'TKT-1040', subject: 'API rate limit exceeded — production impact', customer: 'Carol Smith', customerEmail: 'carol@techcorp.com', customerCompany: 'TechCorp', priority: 'critical', status: 'open', category: 'technical', sentiment: 'frustrated', assignee: null, aiConfidence: 0.97, aiSuggestedCategory: 'technical', aiSuggestedRouting: 'Platform Engineering', aiPredictionAccepted: null, createdAt: '2026-08-11T07:30:00Z', updatedAt: '2026-08-11T07:30:00Z', slaDeadline: '2026-08-11T11:30:00Z', slaBreached: true, tags: ['api', 'rate-limit', 'urgent'], messages: baseMessages('Carol Smith', 'Our production integration is being rate-limited and customers are seeing errors right now.'), activity: baseActivity('Unassigned') },
  { id: 'TKT-1039', subject: 'Integration with Salesforce not syncing', customer: 'David Lee', customerEmail: 'david@enterprise.co', customerCompany: 'Enterprise Co', priority: 'medium', status: 'pending', category: 'technical', sentiment: 'neutral', assignee: 'Sarah Chen', aiConfidence: 0.82, aiSuggestedCategory: 'technical', aiSuggestedRouting: 'Integrations Team', aiPredictionAccepted: true, createdAt: '2026-08-10T16:20:00Z', updatedAt: '2026-08-11T08:15:00Z', slaDeadline: '2026-08-12T16:20:00Z', slaBreached: false, tags: ['integration', 'salesforce'], messages: baseMessages('David Lee', 'Salesforce sync stopped working two days ago, contacts are not updating.'), activity: baseActivity('Sarah Chen') },
  { id: 'TKT-1038', subject: 'Request for enterprise plan pricing', customer: 'Eva Wang', customerEmail: 'eva@bigco.com', customerCompany: 'BigCo', priority: 'low', status: 'open', category: 'billing', sentiment: 'positive', assignee: null, aiConfidence: 0.76, aiSuggestedCategory: 'billing', aiSuggestedRouting: 'Sales / Billing', aiPredictionAccepted: null, createdAt: '2026-08-10T14:00:00Z', updatedAt: '2026-08-10T14:00:00Z', slaDeadline: '2026-08-13T14:00:00Z', slaBreached: false, tags: ['enterprise', 'pricing'], messages: baseMessages('Eva Wang', 'Could you send over enterprise plan pricing for a 200-seat team?'), activity: baseActivity('Unassigned') },
  { id: 'TKT-1037', subject: 'Export to CSV not working in Firefox', customer: 'Frank Davis', customerEmail: 'frank@media.net', customerCompany: 'Media Net', priority: 'medium', status: 'in_progress', category: 'technical', sentiment: 'neutral', assignee: 'James Park', aiConfidence: 0.91, aiSuggestedCategory: 'technical', aiSuggestedRouting: 'Platform Engineering', aiPredictionAccepted: true, createdAt: '2026-08-10T11:30:00Z', updatedAt: '2026-08-11T07:00:00Z', slaDeadline: '2026-08-12T11:30:00Z', slaBreached: false, tags: ['browser', 'export'], messages: baseMessages('Frank Davis', 'CSV export button does nothing on Firefox 128, works fine on Chrome.'), activity: baseActivity('James Park') },
  { id: 'TKT-1036', subject: 'Incorrect tax calculation on EU invoices', customer: 'Grace Kim', customerEmail: 'grace@shop.eu', customerCompany: 'Shop EU', priority: 'high', status: 'resolved', category: 'billing', sentiment: 'negative', assignee: 'Sarah Chen', aiConfidence: 0.85, aiSuggestedCategory: 'billing', aiSuggestedRouting: 'Billing Team', aiPredictionAccepted: true, createdAt: '2026-08-09T09:00:00Z', updatedAt: '2026-08-10T15:30:00Z', slaDeadline: '2026-08-10T09:00:00Z', slaBreached: false, tags: ['tax', 'eu', 'billing'], messages: baseMessages('Grace Kim', 'VAT is being calculated incorrectly on our last 3 invoices.'), activity: baseActivity('Sarah Chen') },
  { id: 'TKT-1035', subject: 'Mobile app crashes on iOS 17.5', customer: 'Henry Brown', customerEmail: 'henry@user.com', customerCompany: 'Individual', priority: 'high', status: 'open', category: 'technical', sentiment: 'frustrated', assignee: null, aiConfidence: 0.89, aiSuggestedCategory: 'technical', aiSuggestedRouting: 'Mobile Team', aiPredictionAccepted: null, createdAt: '2026-08-09T08:00:00Z', updatedAt: '2026-08-09T08:00:00Z', slaDeadline: '2026-08-10T08:00:00Z', slaBreached: true, tags: ['mobile', 'ios', 'crash'], messages: baseMessages('Henry Brown', 'App crashes immediately on launch since updating to iOS 17.5.'), activity: baseActivity('Unassigned') },
]

// ─── Team ────────────────────────────────────────────────────────────────────

export const mockTeam: TeamMember[] = [
  { id: 'u1', name: 'Sarah Chen',  email: 'sarah@triageflow.io',  role: 'team_lead', avatar: 'SC', activeTickets: 12, resolvedToday: 8,  avgHandleTime: '18m', status: 'online'  },
  { id: 'u2', name: 'James Park',  email: 'james@triageflow.io',  role: 'agent',     avatar: 'JP', activeTickets: 9,  resolvedToday: 11, avgHandleTime: '22m', status: 'online'  },
  { id: 'u3', name: 'Maria Lopez', email: 'maria@triageflow.io',  role: 'agent',     avatar: 'ML', activeTickets: 7,  resolvedToday: 6,  avgHandleTime: '31m', status: 'away'   },
  { id: 'u4', name: 'Tom Hughes',  email: 'tom@triageflow.io',    role: 'agent',     avatar: 'TH', activeTickets: 5,  resolvedToday: 14, avgHandleTime: '15m', status: 'online'  },
  { id: 'u5', name: 'Priya Nair',  email: 'priya@triageflow.io',  role: 'admin',     avatar: 'PN', activeTickets: 0,  resolvedToday: 0,  avgHandleTime: '—',   status: 'online'  },
]

// ─── Overview stats ──────────────────────────────────────────────────────────

export const overviewStats = {
  openTickets: 247,
  openDelta: +12,
  avgResponseTime: '4m 38s',
  responseDelta: -23,
  slaCompliance: 94.2,
  slaDelta: +1.8,
  aiAccuracy: 91.7,
  aiDelta: +0.4,
  resolvedToday: 183,
  resolvedDelta: +29,
  criticalOpen: 8,
}

// ─── Chart data ───────────────────────────────────────────────────────────────

export const ticketVolumeData: MetricPoint[] = [
  { date: 'Aug 5',  value: 210 },
  { date: 'Aug 6',  value: 195 },
  { date: 'Aug 7',  value: 238 },
  { date: 'Aug 8',  value: 175 },
  { date: 'Aug 9',  value: 189 },
  { date: 'Aug 10', value: 224 },
  { date: 'Aug 11', value: 247 },
]

export const aiAccuracyData: MetricPoint[] = [
  { date: 'Aug 5',  value: 88.2 },
  { date: 'Aug 6',  value: 89.1 },
  { date: 'Aug 7',  value: 90.4 },
  { date: 'Aug 8',  value: 89.8 },
  { date: 'Aug 9',  value: 91.0 },
  { date: 'Aug 10', value: 91.3 },
  { date: 'Aug 11', value: 91.7 },
]

export const f1ScoreData: MetricPoint[] = [
  { date: 'Aug 5',  value: 86.9 },
  { date: 'Aug 6',  value: 87.8 },
  { date: 'Aug 7',  value: 89.0 },
  { date: 'Aug 8',  value: 88.6 },
  { date: 'Aug 9',  value: 90.1 },
  { date: 'Aug 10', value: 91.0 },
  { date: 'Aug 11', value: 91.7 },
]

export const latencyData: MetricPoint[] = [
  { date: 'Aug 5',  value: 142 },
  { date: 'Aug 6',  value: 138 },
  { date: 'Aug 7',  value: 151 },
  { date: 'Aug 8',  value: 129 },
  { date: 'Aug 9',  value: 134 },
  { date: 'Aug 10', value: 121 },
  { date: 'Aug 11', value: 118 },
]

export const dataFreshnessData: MetricPoint[] = [
  { date: 'Aug 5',  value: 26 },
  { date: 'Aug 6',  value: 22 },
  { date: 'Aug 7',  value: 30 },
  { date: 'Aug 8',  value: 18 },
  { date: 'Aug 9',  value: 14 },
  { date: 'Aug 10', value: 20 },
  { date: 'Aug 11', value: 9 },
]

export const categoryDistribution = [
  { name: 'Technical',  value: 38, color: '#3366ff' },
  { name: 'Billing',    value: 27, color: '#f59e0b' },
  { name: 'Account',    value: 18, color: '#10b981' },
  { name: 'General',    value: 11, color: '#8b5cf6' },
  { name: 'Shipping',   value: 6,  color: '#ef4444'  },
]

export const slaData = [
  { date: 'Aug 5',  met: 92, breached: 8 },
  { date: 'Aug 6',  met: 95, breached: 5 },
  { date: 'Aug 7',  met: 91, breached: 9 },
  { date: 'Aug 8',  met: 96, breached: 4 },
  { date: 'Aug 9',  met: 93, breached: 7 },
  { date: 'Aug 10', met: 94, breached: 6 },
  { date: 'Aug 11', met: 94, breached: 6 },
]

export interface ModelVersionEntry {
  version: string
  deployedAt: string
  accuracy: number
  f1: number
  status: 'active' | 'archived' | 'candidate'
  trainingExamples: number
}

export const modelVersionHistory: ModelVersionEntry[] = [
  { version: 'v3.2.1', deployedAt: '2026-08-08T02:00:00Z', accuracy: 0.934, f1: 0.917, status: 'active', trainingExamples: 14820 },
  { version: 'v3.1.0', deployedAt: '2026-07-22T02:00:00Z', accuracy: 0.921, f1: 0.903, status: 'archived', trainingExamples: 13940 },
  { version: 'v3.0.4', deployedAt: '2026-07-05T02:00:00Z', accuracy: 0.912, f1: 0.891, status: 'archived', trainingExamples: 12610 },
  { version: 'v2.9.2', deployedAt: '2026-06-18T02:00:00Z', accuracy: 0.898, f1: 0.874, status: 'archived', trainingExamples: 11205 },
]

export const modelMetrics = {
  precision: 0.923,
  recall: 0.911,
  f1: 0.917,
  accuracy: 0.934,
  latencyMs: 118,
  dataFreshnessHours: 9,
  lastRetrained: '2026-08-08T02:00:00Z',
  trainingExamples: 14_820,
  pendingFeedback: 142,
  approvedCorrections: 38,
  retrainThreshold: 50,
  modelVersion: 'v3.2.1',
}

export const confusionClasses = ['Billing', 'Technical', 'Account', 'General', 'Shipping']

// Confusion matrix — rows = actual, cols = predicted (counts, mock data)
export const confusionMatrix: number[][] = [
  [214, 6, 3, 2, 1],
  [8, 402, 5, 4, 0],
  [4, 3, 188, 6, 0],
  [2, 5, 4, 121, 1],
  [1, 0, 0, 2, 64],
]

export interface FeedbackItem {
  id: string
  ticketId: string
  aiLabel: string
  agentLabel: string
  confidence: number
  status: 'pending' | 'approved' | 'rejected'
  agent: string
  submittedAt: string
}

export const feedbackItems: FeedbackItem[] = [
  { id: 'fb1', ticketId: 'TKT-1033', aiLabel: 'Technical', agentLabel: 'Billing', confidence: 0.62, status: 'pending', agent: 'James Park',  submittedAt: '2026-08-11T08:00:00Z' },
  { id: 'fb2', ticketId: 'TKT-1031', aiLabel: 'General',   agentLabel: 'Account', confidence: 0.71, status: 'approved', agent: 'Maria Lopez', submittedAt: '2026-08-10T17:30:00Z' },
  { id: 'fb3', ticketId: 'TKT-1028', aiLabel: 'Shipping',  agentLabel: 'Billing', confidence: 0.55, status: 'pending', agent: 'Tom Hughes',  submittedAt: '2026-08-10T14:15:00Z' },
  { id: 'fb4', ticketId: 'TKT-1025', aiLabel: 'Technical', agentLabel: 'Account', confidence: 0.68, status: 'rejected', agent: 'Sarah Chen', submittedAt: '2026-08-10T11:00:00Z' },
  { id: 'fb5', ticketId: 'TKT-1022', aiLabel: 'Billing',   agentLabel: 'Billing', confidence: 0.90, status: 'approved', agent: 'Tom Hughes',  submittedAt: '2026-08-09T13:20:00Z' },
]

// ─── Routing queue ────────────────────────────────────────────────────────────

export interface RoutingRule {
  id: string
  category: TicketCategory
  destination: string
  condition: string
  active: boolean
  ticketsRoutedToday: number
}

export const routingRules: RoutingRule[] = [
  { id: 'rr1', category: 'technical', destination: 'Platform Engineering', condition: 'confidence >= 0.80', active: true, ticketsRoutedToday: 62 },
  { id: 'rr2', category: 'billing',   destination: 'Billing Team',         condition: 'confidence >= 0.75', active: true, ticketsRoutedToday: 44 },
  { id: 'rr3', category: 'account',   destination: 'Account & Access Team', condition: 'confidence >= 0.80', active: true, ticketsRoutedToday: 31 },
  { id: 'rr4', category: 'shipping',  destination: 'Logistics Support',    condition: 'confidence >= 0.70', active: true, ticketsRoutedToday: 9 },
  { id: 'rr5', category: 'general',   destination: 'Tier 1 Support',       condition: 'confidence < 0.70 (fallback)', active: true, ticketsRoutedToday: 18 },
]

// ─── Integrations ─────────────────────────────────────────────────────────────

export interface Integration {
  id: string
  name: string
  category: 'ingestion' | 'notification' | 'crm' | 'auth'
  status: 'connected' | 'disconnected' | 'error'
  description: string
  lastSync: string | null
}

export const integrations: Integration[] = [
  { id: 'int1', name: 'Email Ingestion (IMAP)', category: 'ingestion', status: 'connected', description: 'Ingests support tickets from support@triageflow.io', lastSync: '2026-08-11T09:10:00Z' },
  { id: 'int2', name: 'Webhook Ingestion', category: 'ingestion', status: 'connected', description: 'Accepts inbound tickets via POST /integrations/webhook', lastSync: '2026-08-11T09:08:00Z' },
  { id: 'int3', name: 'Slack Alerts', category: 'notification', status: 'connected', description: 'Sends SLA breach and critical ticket alerts to #support-alerts', lastSync: '2026-08-11T08:55:00Z' },
  { id: 'int4', name: 'Salesforce', category: 'crm', status: 'error', description: 'Syncs customer and account records', lastSync: '2026-08-09T12:00:00Z' },
  { id: 'int5', name: 'SSO (SAML)', category: 'auth', status: 'disconnected', description: 'Single sign-on for team members', lastSync: null },
]

// ─── Roles & permissions ───────────────────────────────────────────────────────

export interface PermissionRow {
  action: string
  agent: boolean
  team_lead: boolean
  admin: boolean
}

export const permissionMatrix: PermissionRow[] = [
  { action: 'View assigned tickets', agent: true, team_lead: true, admin: true },
  { action: 'View all team tickets', agent: false, team_lead: true, admin: true },
  { action: 'Correct AI category / accept prediction', agent: true, team_lead: true, admin: true },
  { action: 'Reassign tickets across agents', agent: false, team_lead: true, admin: true },
  { action: 'Approve / reject feedback for retraining', agent: false, team_lead: true, admin: true },
  { action: 'Trigger manual retraining run', agent: false, team_lead: false, admin: true },
  { action: 'Manage routing rules', agent: false, team_lead: true, admin: true },
  { action: 'Manage integrations & API keys', agent: false, team_lead: false, admin: true },
  { action: 'Manage team members & roles', agent: false, team_lead: false, admin: true },
]

// ─── Notifications ─────────────────────────────────────────────────────────────

export interface NotificationItem {
  id: string
  title: string
  detail: string
  timestamp: string
  read: boolean
  severity: 'info' | 'warning' | 'critical'
}

export const initialNotifications: NotificationItem[] = [
  { id: 'n1', title: 'SLA breach', detail: 'TKT-1040 has breached its SLA deadline', timestamp: '2026-08-11T11:31:00Z', read: false, severity: 'critical' },
  { id: 'n2', title: 'Retraining threshold reached', detail: '38 of 50 approved corrections collected', timestamp: '2026-08-11T09:00:00Z', read: false, severity: 'warning' },
  { id: 'n3', title: 'New model deployed', detail: 'v3.2.1 is now active', timestamp: '2026-08-08T02:05:00Z', read: true, severity: 'info' },
]
