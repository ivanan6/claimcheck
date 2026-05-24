import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Scale, ShieldCheck, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react'

const AGENT_META = {
  1: { icon: Brain, title: 'Agent 1 · Medical Coder', subtitle: 'Gemini cita lekarski nalaz' },
  2: { icon: Scale, title: 'Agent 2 · Contract Lawyer', subtitle: 'Graph RAG nad ugovorom' },
  3: { icon: ShieldCheck, title: 'Agent 3 · Auditor', subtitle: 'Unakrsna provera' },
}

export default function AgentCard({ agentNumber, state, result }) {
  const meta = AGENT_META[agentNumber]
  const Icon = meta.icon

  const stateStyles = {
    idle: 'border-aegis-border',
    running: 'glow-cyan',
    done: 'glow-green',
    flagged: 'glow-red',
  }

  return (
    <motion.div layout className={`bg-aegis-panel2 rounded-xl border-2 transition-all duration-300 ${stateStyles[state]}`}>
      <div className="p-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center ${
              state === 'idle' ? 'bg-aegis-border text-aegis-muted'
              : state === 'flagged' ? 'bg-aegis-danger/20 text-aegis-danger'
              : state === 'done' ? 'bg-aegis-success/20 text-aegis-success'
              : 'bg-aegis-accent/20 text-aegis-accent'
            }`}
          >
            <Icon size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm">{meta.title}</div>
            <div className="text-[11px] text-aegis-muted">{meta.subtitle}</div>
          </div>
          <StatusBadge state={state} />
        </div>

        <AnimatePresence>
          {state !== 'idle' && result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 pt-3 border-t border-aegis-border overflow-hidden"
            >
              {agentNumber === 1 && <Agent1Result findings={result} />}
              {agentNumber === 2 && <Agent2Result rules={result} />}
              {agentNumber === 3 && <Agent3Result issues={result} />}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

function StatusBadge({ state }) {
  if (state === 'idle') return <span className="text-[10px] text-aegis-muted">CEKA</span>
  if (state === 'running')
    return (
      <span className="flex items-center gap-1 text-[10px] text-aegis-accent">
        <Loader2 size={10} className="animate-spin" /> ANALIZIRA
      </span>
    )
  if (state === 'done')
    return (
      <span className="flex items-center gap-1 text-[10px] text-aegis-success">
        <CheckCircle2 size={10} /> GOTOVO
      </span>
    )
  if (state === 'flagged')
    return (
      <span className="flex items-center gap-1 text-[10px] text-aegis-danger">
        <AlertTriangle size={10} /> GRESKE
      </span>
    )
  return null
}

function Agent1Result({ findings }) {
  if (!findings || findings.length === 0)
    return <div className="text-xs text-aegis-muted italic">Nije nasao klinicke nalaze.</div>
  return (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase tracking-wider text-aegis-muted">
        Izvuceno iz teksta lekara:
      </div>
      {findings.map((f, i) => (
        <div key={i} className="text-xs bg-aegis-panel rounded p-2 border border-aegis-border">
          <div className="flex items-center gap-2">
            <span className="font-mono text-aegis-accent font-bold">{f.suggested_icd10}</span>
            <span className="text-aegis-text">{f.finding}</span>
            <span className="ml-auto text-[10px] text-aegis-muted">
              {Math.round(f.confidence * 100)}%
            </span>
          </div>
          {f.evidence_quote && (
            <div className="mt-1 text-[10px] italic text-aegis-muted">"{f.evidence_quote}"</div>
          )}
        </div>
      ))}
    </div>
  )
}

function Agent2Result({ rules }) {
  if (!rules || rules.length === 0)
    return <div className="text-xs text-aegis-muted italic">Nije nasao pravila.</div>
  return (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase tracking-wider text-aegis-muted">
        Pravila iz ugovora:
      </div>
      {rules.map((r, i) => (
        <div key={i} className="text-xs bg-aegis-panel rounded p-2 border border-aegis-border">
          <div className="flex items-center gap-2">
            <span className="font-mono text-aegis-accent2 font-bold">{r.rule_id}</span>
            <span className="text-aegis-text">→ CPT {r.procedure_cpt}</span>
          </div>
          {r.requires_icd10_categories?.length > 0 && (
            <div className="mt-1 text-[10px] text-aegis-muted">
              Zahteva ICD-10:{' '}
              <span className="font-mono">{r.requires_icd10_categories.join(', ')}</span>
            </div>
          )}
          {r.additional_constraint && (
            <div className="mt-0.5 text-[10px] text-aegis-warning">
              Dodatno: {r.additional_constraint}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function Agent3Result({ issues }) {
  if (!issues || issues.length === 0)
    return (
      <div className="text-xs text-aegis-success italic flex items-center gap-1">
        <CheckCircle2 size={12} /> Nema nepravilnosti. Racun je cist.
      </div>
    )
  return (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase tracking-wider text-aegis-danger">
        Pronadjene greske:
      </div>
      {issues.map((iss, i) => (
        <div key={i} className="text-xs bg-aegis-danger/10 rounded p-2 border border-aegis-danger/30">
          <div className="font-semibold text-aegis-danger">
            CPT {iss.line_item_cpt} · {iss.issue_type}
          </div>
          <div className="mt-1 text-aegis-text">{iss.explanation}</div>
        </div>
      ))}
    </div>
  )
}
