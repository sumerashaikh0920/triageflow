import { cn } from '@/lib/utils'

interface AvatarProps {
  initials: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  status?: 'online' | 'away' | 'offline'
}

const sizeMap = { sm: 'w-7 h-7 text-xs', md: 'w-9 h-9 text-sm', lg: 'w-11 h-11 text-base' }
const statusMap = { online: 'bg-emerald-500', away: 'bg-amber-500', offline: 'bg-gray-400' }

const colors = [
  'bg-brand-600 text-white',
  'bg-emerald-600 text-white',
  'bg-violet-600 text-white',
  'bg-amber-600 text-white',
  'bg-rose-600 text-white',
  'bg-sky-600 text-white',
]

function getColor(initials: string) {
  const idx = initials.charCodeAt(0) % colors.length
  return colors[idx]
}

export function Avatar({ initials, size = 'md', className, status }: AvatarProps) {
  return (
    <span className={cn('relative inline-flex items-center justify-center rounded-full font-semibold select-none', sizeMap[size], getColor(initials), className)}>
      {initials}
      {status && (
        <span className={cn('absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-card', statusMap[status])} />
      )}
    </span>
  )
}
