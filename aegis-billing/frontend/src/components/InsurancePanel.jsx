import { Landmark, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import PanelShell from './PanelShell'
import { Card } from '@/components/ui/card'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

export default function InsurancePanel({ packet, decision }) {
  const status = !decision ? 'waiting' : decision.status

  return (
    <PanelShell
      stepLabel="03"
      icon={Landmark}
      title="Insurance"
      subtitle={packet?.insurance_company || 'Global Health Insurance'}
    >
      <div className="flex-1 flex flex-col">
        <AnimatePresence mode="wait">
          {status === 'waiting' && <WaitingState key="waiting" />}
          {status === 'approved' && <ApprovedState key="approved" packet={packet} decision={decision} />}
          {status === 'rejected' && <RejectedState key="rejected" packet={packet} decision={decision} />}
        </AnimatePresence>
      </div>
    </PanelShell>
  )
}

function WaitingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex-1 flex flex-col items-center justify-center text-center py-12"
    >
      <div className="w-14 h-14 rounded-2xl bg-secondary border border-border flex items-center justify-center text-muted-foreground mb-4">
        <Clock size={24} />
      </div>
      <div className="text-sm text-foreground font-semibold">Insurance inbox</div>
      <div className="text-[11px] text-muted-foreground mt-1">
        Waiting for a new request from the clearinghouse...
      </div>
    </motion.div>
  )
}

function ApprovedState({ packet, decision }) {
  const total = packet.bill_items.reduce((s, i) => s + i.unit_price_eur * i.quantity, 0)
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex-1 flex flex-col"
    >
      <Alert variant="success" className="mb-4">
        <CheckCircle2 className="h-5 w-5" />
        <AlertTitle>BILL RECEIVED</AlertTitle>
        <AlertDescription>Validation passed, payout started</AlertDescription>
      </Alert>

      <Card className="p-4 space-y-3 bg-secondary/40">
        <Row label="Packet ID" value={packet.packet_id} mono />
        <Row label="Clinic" value={packet.clinic_name} />
        <Row label="Patient" value={packet.patient.full_name} />
        <Row label="Procedure" value={packet.bill_items.map((i) => i.cpt_code).join(', ')} mono />
        <div className="pt-3 border-t border-border">
          <Row label="Payout amount" value={`${total.toFixed(2)} €`} highlight />
          <Row label="Expected payout" value="in 7-14 days" />
        </div>
      </Card>

      <div className="mt-auto pt-4 text-center text-[11px] text-muted-foreground">
        Processed in {(decision.processing_time_ms / 1000).toFixed(1)}s ·
        AI validation: <span className="text-aegis-success font-bold">PASSED</span>
      </div>
    </motion.div>
  )
}

function RejectedState({ packet, decision }) {
  const isPreAuth = (decision.agent3_issues || []).some(
    (i) => i.issue_type === 'contract_limit_violation'
  )
  const isMissingDocs = (decision.agent3_issues || []).some(
    (i) => i.issue_type === 'missing_required_documentation'
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex-1 flex flex-col"
    >
      <Alert variant="warning" className="mb-4">
        <XCircle className="h-5 w-5" />
        <AlertTitle>
          {isPreAuth
            ? 'REQUEST STOPPED BEFORE PROCEDURE'
            : isMissingDocs
              ? 'PACKAGE INCOMPLETE'
              : 'BILL DID NOT ARRIVE'}
        </AlertTitle>
        <AlertDescription>
          {isPreAuth
            ? 'Aegis intercepted pre-authorization, procedure was not performed'
            : isMissingDocs
              ? 'Aegis predicted missing attachments before insurer denial'
              : 'Stopped in the clearinghouse before sending'}
        </AlertDescription>
      </Alert>

      {isPreAuth ? (
        <Card className="p-4 bg-secondary/40">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-3">
            What Aegis saved
          </div>
          <ul className="space-y-2.5 text-sm">
            <ImpactItem tone="success">
              Procedure has NOT been performed yet - MRI appointment was not scheduled
            </ImpactItem>
            <ImpactItem tone="success">
              Clinic actually saves{' '}
              <span className="font-bold text-aegis-success font-mono">
                {decision.estimated_saved_eur.toFixed(0)} €
              </span>{' '}
              (machine + radiologist + time)
            </ImpactItem>
            <ImpactItem tone="success">
              Patient notified in advance - can choose to self-pay or cancel
            </ImpactItem>
          </ul>
          <div className="mt-4 pt-3 border-t border-border text-[11px] text-foreground/80 flex items-start gap-2">
            <span className="text-accent font-bold">→</span>
            <span>
              Without Aegis: MRI is performed, the bill is sent, denial arrives
              30-60 days later, and the clinic writes off the loss.
            </span>
          </div>
        </Card>
      ) : isMissingDocs ? (
        <Card className="p-4 bg-secondary/40">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-3">
            What Aegis prevented
          </div>
          <ul className="space-y-2.5 text-sm">
            <ImpactItem tone="success">
              Claim was not sent with an incomplete document package
            </ImpactItem>
            <ImpactItem tone="success">
              Clinic can attach the missing reports before submission
            </ImpactItem>
            <ImpactItem tone="success">
              Avoids a predictable insurer denial and rework cycle
            </ImpactItem>
          </ul>
          <div className="mt-4 pt-3 border-t border-border text-[11px] flex items-start gap-2 text-aegis-success">
            <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
            <span>
              Aegis turned the policy rule into a submission checklist in{' '}
              <span className="font-mono font-bold">
                {(decision.processing_time_ms / 1000).toFixed(1)}s
              </span>
              .
            </span>
          </div>
        </Card>
      ) : (
        <Card className="p-4 bg-secondary/40">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-3">
            Contrast: without AegisBilling.ai
          </div>
          <ul className="space-y-2.5 text-sm">
            <ImpactItem tone="danger">Poorly prepared bill would reach us</ImpactItem>
            <ImpactItem tone="danger">Automatic denial generated in 30 days</ImpactItem>
            <ImpactItem tone="danger">
              Clinic loses{' '}
              <span className="font-bold text-foreground font-mono">
                {decision.estimated_saved_eur.toFixed(2)} €
              </span>{' '}
              and spends a week writing an appeal
            </ImpactItem>
          </ul>
          <div className="mt-4 pt-3 border-t border-border text-[11px] flex items-start gap-2 text-aegis-success">
            <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
            <span>
              Aegis stopped the bill in{' '}
              <span className="font-mono font-bold">
                {(decision.processing_time_ms / 1000).toFixed(1)}s
              </span>
              . Front-desk staff get an auto-fix suggestion on screen.
            </span>
          </div>
        </Card>
      )}
    </motion.div>
  )
}

function ImpactItem({ tone, children }) {
  const bullet = tone === 'danger' ? (
    <span className="text-aegis-danger mt-0.5">●</span>
  ) : (
    <CheckCircle2 size={14} className="text-aegis-success mt-0.5 shrink-0" />
  )
  return (
    <li className="flex gap-2 items-start text-foreground/80 text-[13px] leading-snug">
      {bullet}
      <span>{children}</span>
    </li>
  )
}

function Row({ label, value, mono, highlight }) {
  return (
    <div className="flex justify-between items-center gap-3 text-sm">
      <span className="text-muted-foreground text-[11px] uppercase tracking-wider font-semibold">
        {label}
      </span>
      <span
        className={`${mono ? 'font-mono text-xs' : ''} ${
          highlight ? 'font-bold text-aegis-success text-base' : 'text-foreground'
        }`}
      >
        {value}
      </span>
    </div>
  )
}
