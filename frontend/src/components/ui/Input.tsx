import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface InputProps extends HTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full rounded-lg border bg-white text-neutral-900 placeholder:text-neutral-400',
              'focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary',
              'disabled:bg-neutral-100 disabled:cursor-not-allowed',
              'transition-colors duration-200',
              icon && 'pl-10',
              error && 'border-danger focus:ring-danger/50 focus:border-danger',
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'



