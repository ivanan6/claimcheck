import { Play, Loader2 } from 'lucide-react'

export default function ScenarioSelector({ scenarios, selectedId, onSelect, onRun, running }) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex gap-2 flex-wrap">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            disabled={running}
            className={`px-3 py-2 rounded-lg border text-sm transition disabled:opacity-50 ${
              selectedId === s.id
                ? 'border-aegis-accent bg-aegis-accent/10 text-aegis-accent'
                : 'border-aegis-border bg-aegis-panel2 text-aegis-text hover:border-aegis-accent/50'
            }`}
          >
            <div className="font-semibold leading-tight">{s.name}</div>
            <div className="text-[10px] text-aegis-muted mt-0.5">{s.subtitle}</div>
          </button>
        ))}
      </div>

      <button
        onClick={onRun}
        disabled={!selectedId || running}
        className="ml-auto px-5 py-2.5 rounded-lg bg-aegis-accent text-aegis-bg font-bold hover:bg-aegis-accent/90 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {running ? <><Loader2 size={16} className="animate-spin" />Pokrecem...</> : <><Play size={16} fill="currentColor" />POKRENI DEMO</>}
      </button>
    </div>
  )
}
