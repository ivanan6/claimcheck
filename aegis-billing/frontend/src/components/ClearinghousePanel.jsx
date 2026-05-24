import { Network } from 'lucide-react'
import AgentCard from './AgentCard'
import PanelShell from './PanelShell'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function ClearinghousePanel({ agentStates, agentResults, decision }) {
  return (
    <PanelShell
      stepLabel="02"
      icon={Network}
      title="Clearinghouse"
      subtitle="AegisBilling.ai AI filter"
      headerRight={<LiveBadge agentStates={agentStates} decision={decision} />}
    >
      <div className="flex-1 space-y-3">
        <AgentCard agentNumber={1} state={agentStates[1]} result={agentResults[1]} />
        <AgentCard agentNumber={2} state={agentStates[2]} result={agentResults[2]} />
        <AgentCard agentNumber={3} state={agentStates[3]} result={agentResults[3]} />
      </div>

      {decision && (
        <div className="mt-4 pt-4 border-t border-border">
          <DecisionFooter decision={decision} />
        </div>
      )}
    </PanelShell>
  )
}

function LiveBadge({ agentStates, decision }) {
  const isRunning = Object.values(agentStates).some((s) => s === 'running')
  if (isRunning)
    return (
      <Badge variant="live">
        <span className="w-1.5 h-1.5 rounded-full bg-aegis-accent animate-pulse mr-0.5" />
        Live
      </Badge>
    )
  if (decision?.status === 'approved') return <Badge variant="success">Approved</Badge>
  if (decision?.status === 'rejected') return <Badge variant="danger">Blocked</Badge>
  return <Badge variant="outline" className="text-muted-foreground">Idle</Badge>
}

function DecisionFooter({ decision }) {
  const approved = decision.status === 'approved'
  return (
    <div className="grid grid-cols-3 gap-2">
      <FooterStat label="Status" value={approved ? 'ACCEPTED' : 'STOP'} tone={approved ? 'success' : 'danger'} />
      <FooterStat label="Time" value={`${(decision.processing_time_ms / 1000).toFixed(1)}s`} tone="primary" />
      <FooterStat label="Saved" value={`${decision.estimated_saved_eur.toFixed(0)} €`} tone="accent" />
    </div>
  )
}

const TONES = {
  primary: 'text-primary',
  accent: 'text-accent',
  success: 'text-aegis-success',
  danger: 'text-aegis-danger',
}

function FooterStat({ label, value, tone }) {
  return (
    <Card className="p-2.5 text-center bg-secondary/40">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
        {label}
      </div>
      <div className={`text-sm font-bold ${TONES[tone]} font-mono mt-0.5`}>{value}</div>
    </Card>
  )
}
