import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const alertVariants = cva(
  'relative w-full rounded-xl border p-4 [&>svg~*]:pl-8 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4',
  {
    variants: {
      variant: {
        default: 'bg-card text-foreground border-border [&>svg]:text-foreground',
        info: 'bg-secondary border-primary/20 text-primary [&>svg]:text-primary',
        warning: 'bg-aegis-warning-soft border-aegis-warning/30 text-aegis-warning [&>svg]:text-aegis-warning',
        destructive: 'bg-aegis-danger-soft border-aegis-danger/30 text-aegis-danger [&>svg]:text-aegis-danger',
        success: 'bg-aegis-success-soft border-aegis-success/30 text-aegis-success [&>svg]:text-aegis-success',
        accent: 'bg-aegis-accent-soft border-aegis-accent/30 text-aegis-accent [&>svg]:text-aegis-accent',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

const Alert = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
))
Alert.displayName = 'Alert'

const AlertTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn('mb-1 font-bold text-sm leading-none tracking-tight', className)}
    {...props}
  />
))
AlertTitle.displayName = 'AlertTitle'

const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('text-xs leading-relaxed [&_p]:leading-relaxed', className)} {...props} />
))
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertTitle, AlertDescription }
