import { motion, AnimatePresence } from 'framer-motion'
import {
  BrainCircuit, Scale, ShieldCheck, Loader2, CheckCircle2, AlertTriangle, Quote,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const AGENT_META = {
  1: { icon: BrainCircuit, title: 'Medical Coder', subtitle: 'Reads doctor\'s note (LLM)' },
  2: { icon: Scale, title: 'Contract Lawyer', subtitle: 'Searches the contract (Graph RAG)' },
  3: { icon: ShieldCheck, title: 'Auditor', subtitle: 'Cross-checks the bill' },
}

const STATE_RING = {
  idle: 'border-border',
  running: 'border-primary/40 ring-2 ring-primary/10',
  done: 'border-aegis-success/40 ring-2 ring-aegis-success/10',
  flagged: 'border-aegis-danger/40 ring-2 ring-aegis-danger/10',
}

const STATE_ICON_BG = {
  idle: 'bg-card border border-border text-muted-foreground',
  running: 'bg-aegis-accent-soft text-aegis-accent',
  done: 'bg-aegis-success-soft text-aegis-success',
  flagged: 'bg-aegis-danger-soft text-aegis-danger',
}

export default function AgentCard({ agentNumber, state, result }) {
  const meta = AGENT_META[agentNumber]
  const Icon = meta.icon

  return (
    <motion.div layout>
      <Card className={cn('transition-all duration-300 border-2', STATE_RING[state])}>
        <div className="p-4">
          <div className="flex items-center gap-3">
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', STATE_ICON_BG[state])}>
              <Icon size={18} strokeWidth={2.2} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[10px] font-mono font-bold text-muted-foreground/80">
                AGENT 0{agentNumber}
              </div>
              <div className="font-semibold text-sm text-foreground leading-tight">{meta.title}</div>
              <div className="text-[11px] text-muted-foreground">{meta.subtitle}</div>
            </div>
            <StatusBadge state={state} />
          </div>

          <AnimatePresence>
            {state !== 'idle' && result && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 pt-3 border-t border-border overflow-hidden"
              >
                {agentNumber === 1 && <Agent1Result findings={result} />}
                {agentNumber === 2 && <Agent2Result rules={result} />}
                {agentNumber === 3 && <Agent3Result issues={result} />}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Card>
    </motion.div>
  )
}

function StatusBadge({ state }) {
  if (state === 'idle')
    return <Badge variant="outline" className="text-muted-foreground">Waiting</Badge>
  if (state === 'running')
    return (
      <Badge variant="default" className="bg-primary/10 text-primary border-transparent">
        <Loader2 size={11} className="animate-spin" /> Analyzing
      </Badge>
    )
  if (state === 'done')
    return <Badge variant="success"><CheckCircle2 size={11} /> Done</Badge>
  if (state === 'flagged')
    return <Badge variant="danger"><AlertTriangle size={11} /> Errors</Badge>
  return null
}

function Agent1Result({ findings }) {
  if (!findings || findings.length === 0)
    return <EmptyResult>No clinical findings found.</EmptyResult>
  return (
    <ResultSection label="Extracted from physician note">
      {findings.map((f, i) => (
        <div key={i} className="bg-card rounded-lg p-2.5 border border-border">
          <div className="flex items-center gap-2">
            <Badge variant="live" className="font-mono">{f.suggested_icd10}</Badge>
            <span className="text-xs text-foreground font-medium flex-1">{f.finding}</span>
            <span className="text-[10px] text-muted-foreground font-mono shrink-0">
              {Math.round(f.confidence * 100)}%
            </span>
          </div>
          {f.evidence_quote && (
            <div className="mt-1.5 text-[10px] text-muted-foreground italic flex gap-1 leading-snug">
              <Quote size={10} className="shrink-0 mt-0.5" />
              <span>"{f.evidence_quote}"</span>
            </div>
          )}
        </div>
      ))}
    </ResultSection>
  )
}

function Agent2Result({ rules }) {
  if (!rules || rules.length === 0)
    return <EmptyResult>No rules found.</EmptyResult>
  return (
    <ResultSection label="Contract rules">
      {rules.map((r, i) => (
        <div key={i} className="bg-card rounded-lg p-2.5 border border-border">
          <div className="flex items-center gap-2">
            <Badge variant="default" className="bg-primary/10 text-primary border-transparent font-mono">
              {r.rule_id}
            </Badge>
            <span className="text-xs text-foreground font-medium">→ CPT {r.procedure_cpt}</span>
          </div>
          {r.requires_icd10_categories?.length > 0 && (
            <div className="mt-1 text-[10px] text-muted-foreground">
              Requires ICD-10:{' '}
              <span className="font-mono text-foreground/70">{r.requires_icd10_categories.join(', ')}</span>
            </div>
          )}
          {r.additional_constraint && (
            <div className="mt-0.5 text-[10px] text-aegis-warning">{r.additional_constraint}</div>
          )}
        </div>
      ))}
    </ResultSection>
  )
}

function Agent3Result({ issues }) {
  if (!issues || issues.length === 0)
    return (
      <div className="flex items-center gap-2 text-xs text-aegis-success font-medium">
        <CheckCircle2 size={14} /> No irregularities. The bill is clean.
      </div>
    )
  return (
    <ResultSection label="Errors found" tone="danger">
      {issues.map((iss, i) => (
        <div key={i} className="bg-aegis-danger-soft rounded-lg p-2.5 border border-aegis-danger/20">
          <div className="font-semibold text-aegis-danger text-xs font-mono uppercase tracking-wider">
            CPT {iss.line_item_cpt} · {iss.issue_type.replace(/_/g, ' ')}
          </div>
          <div className="mt-1 text-xs text-foreground leading-snug">{iss.explanation}</div>
        </div>
      ))}
    </ResultSection>
  )
}

function ResultSection({ label, tone = 'muted', children }) {
  const labelColor = tone === 'danger' ? 'text-aegis-danger' : 'text-muted-foreground'
  return (
    <div className="space-y-1.5">
      <div className={cn('text-[10px] uppercase tracking-wider font-bold', labelColor)}>{label}</div>
      {children}
    </div>
  )
}

function EmptyResult({ children }) {
  return <div className="text-xs text-muted-foreground italic">{children}</div>
}
