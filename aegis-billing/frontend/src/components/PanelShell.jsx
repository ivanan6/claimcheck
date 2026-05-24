import { Card } from '@/components/ui/card'

export default function PanelShell({ stepLabel, icon: Icon, title, subtitle, children, headerRight }) {
  return (
    <Card className="relative h-full flex flex-col overflow-hidden">
      <div className="flex items-start gap-3 p-6 pb-4 border-b border-border relative">
        <div className="w-11 h-11 rounded-xl bg-primary/5 flex items-center justify-center text-primary shrink-0">
          <Icon size={20} strokeWidth={2.2} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] uppercase tracking-widest text-accent font-bold">
            Step {stepLabel}
          </div>
          <h2 className="font-bold text-lg leading-tight text-primary tracking-tight">
            {title}
          </h2>
          <p className="text-[11px] text-muted-foreground truncate">{subtitle}</p>
        </div>
        {headerRight}
      </div>

      <div className="flex-1 flex flex-col overflow-y-auto px-6 py-5">{children}</div>
    </Card>
  )
}
