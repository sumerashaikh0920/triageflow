import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg' | 'icon'
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:   'bg-brand-600 text-white hover:bg-brand-700 shadow-sm dark:bg-brand-500 dark:hover:bg-brand-600',
  secondary: 'bg-muted text-foreground hover:bg-muted/80',
  ghost:     'text-foreground hover:bg-muted',
  danger:    'bg-red-600 text-white hover:bg-red-700 shadow-sm',
  outline:   'border border-border text-foreground hover:bg-muted',
}

const sizeClasses: Record<NonNullable<ButtonProps['size']>, string> = {
  sm:   'px-3 py-1.5 text-xs rounded-md gap-1.5',
  md:   'px-4 py-2 text-sm rounded-lg gap-2',
  lg:   'px-5 py-2.5 text-sm rounded-lg gap-2',
  icon: 'p-2 rounded-lg',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'secondary', size = 'md', className, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 disabled:opacity-50 disabled:pointer-events-none',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  ),
)
Button.displayName = 'Button'
