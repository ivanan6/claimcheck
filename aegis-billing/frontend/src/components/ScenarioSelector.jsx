import { Play, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export default function ScenarioSelector({ scenarios, selectedId, onSelect, onRun, running }) {
  return (
    <div className="flex items-center gap-2 flex-wrap ml-auto">
      {scenarios.map((s, i) => (
        <button
          key={s.id}
          onClick={() => onSelect(s.id)}
          disabled={running}
          className={cn(
            'group rounded-xl border px-3.5 py-2.5 text-left transition-all disabled:opacity-50 max-w-[220px]',
            selectedId === s.id
              ? 'border-primary bg-primary text-primary-foreground shadow-md'
              : 'border-border bg-card text-foreground hover:border-primary/40 hover:bg-secondary'
          )}
        >
          <div className="flex items-baseline gap-1.5">
            <span
              className={cn(
                'font-mono font-bold text-[10px]',
                selectedId === s.id ? 'text-aegis-accent2' : 'text-accent'
              )}
            >
              0{i + 1}
            </span>
            <span className="text-[13px] font-semibold leading-tight truncate">{s.name}</span>
          </div>
          <div
            className={cn(
              'text-[10px] mt-0.5 leading-tight truncate',
              selectedId === s.id ? 'text-primary-foreground/70' : 'text-muted-foreground'
            )}
          >
            {s.subtitle}
          </div>
        </button>
      ))}

      <Button
        onClick={onRun}
        disabled={!selectedId || running}
        variant="accent"
        size="lg"
        className="ml-2"
      >
        {running ? (
          <>
            <Loader2 size={16} className="animate-spin" /> Running...
          </>
        ) : (
          <>
            <Play size={16} fill="currentColor" /> Run demo
          </>
        )}
      </Button>
    </div>
  )
}
