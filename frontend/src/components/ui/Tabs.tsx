import { forwardRef, HTMLAttributes, useState } from 'react'
import { cn } from '../../lib/utils'

interface TabsProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onChange'> {
  defaultTab: string
  tabs: { id: string; label: string; icon?: React.ReactNode }[]
  onChange?: (tabId: string) => void
}

export const Tabs = forwardRef<HTMLDivElement, TabsProps>(
  ({ className, defaultTab, tabs, onChange, children, ...props }, ref) => {
    const [activeTab, setActiveTab] = useState(defaultTab)

    return (
      <div ref={ref} className={cn(className)} {...props}>
        <div className="flex gap-1 bg-neutral-100 rounded-lg p-1 mb-4" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => {
                setActiveTab(tab.id)
                onChange?.(tab.id)
              }}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200',
                activeTab === tab.id
                  ? 'bg-white text-brand-primary shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-700'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
        <div role="tabpanel">{children}</div>
      </div>
    )
  }
)

Tabs.displayName = 'Tabs'