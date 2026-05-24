import { Network, Shield } from 'lucide-react'
import AgentCard from './AgentCard'

export default function ClearinghousePanel({ agentStates, agentResults, decision }) {
  return (
    <div className="h-full flex flex-col bg-aegis-panel/80 backdrop-blur-sm rounded-2xl border border-aegis-border p-5 overflow-hidden">
      <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-aegis-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-aegis-accent2/10 flex items-center justify-center text-aegis-accent2">
            <Network size={20} />
          </div>
          <div>
            <h2 className="font-bold text-lg leading-tight">Clearinghouse</h2>
            <p className="text-xs text-aegis-muted">
              <Shield size={10} className="inline mr-1 -mt-0.5" />
              AegisBilling.ai filter
            </p>
          </div>
        </div>
        <LiveBadge agentStates={agentStates} decision={decision} />
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        <AgentCard agentNumber={1} state={agentStates[1]} result={agentResults[1]} />
        <AgentCard agentNumber={2} state={agentStates[2]} result={agentResults[2]} />
        <AgentCard agentNumber={3} state={agentStates[3]} result={agentResults[3]} />
      </div>

      {decision && (
        <div className="mt-4 pt-3 border-t border-aegis-border">
          <DecisionFooter decision={decision} />
        </div>
      )}
    </div>
  )
}

function LiveBadge({ agentStates, decision }) {
  const isRunning = Object.values(agentStates).some((s) => s === 'running')
  if (isRunning)
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-aegis-accent/10 border border-aegis-accent/30 text-[11px] text-aegis-accent">
        <span className="w-1.5 h-1.5 rounded-full bg-aegis-accent animate-pulse" />
        LIVE
      </span>
    )
  if (decision?.status === 'approved')
    return (
      <span className="px-2.5 py-1 rounded-full bg-aegis-success/10 border border-aegis-success/30 text-[11px] text-aegis-success">
        APPROVED
      </span>
    )
  if (decision?.status === 'rejected')
    return (
      <span className="px-2.5 py-1 rounded-full bg-aegis-danger/10 border border-aegis-danger/30 text-[11px] text-aegis-danger">
        BLOKIRAN
      </span>
    )
  return <span className="px-2.5 py-1 rounded-full bg-aegis-border text-[11px] text-aegis-muted">IDLE</span>
}

function DecisionFooter({ decision }) {
  const approved = decision.status === 'approved'
  return (
    <div className="grid grid-cols-3 gap-2 text-center">
      <div className="bg-aegis-panel2 rounded-lg p-2">
        <div className="text-[10px] uppercase text-aegis-muted">Status</div>
        <div className={`text-sm font-bold ${approved ? 'text-aegis-success' : 'text-aegis-danger'}`}>
          {approved ? 'PRIHVACEN' : 'STOP'}
        </div>
      </div>
      <div className="bg-aegis-panel2 rounded-lg p-2">
        <div className="text-[10px] uppercase text-aegis-muted">Vreme</div>
        <div className="text-sm font-bold font-mono text-aegis-text">
          {(decision.processing_time_ms / 1000).toFixed(1)}s
        </div>
      </div>
      <div className="bg-aegis-panel2 rounded-lg p-2">
        <div className="text-[10px] uppercase text-aegis-muted">Sacuvano</div>
        <div className="text-sm font-bold text-aegis-accent">
          {decision.estimated_saved_eur.toFixed(0)} €
        </div>
      </div>
    </div>
  )
}
