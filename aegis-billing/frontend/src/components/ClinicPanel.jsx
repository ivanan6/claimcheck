import {
  Stethoscope, FileText, Receipt, AlertCircle, AlertTriangle,
  Sparkles, Trash2, UserRound, Paperclip,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import PanelShell from './PanelShell'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

export default function ClinicPanel({
  packet,
  highlightMissingIcd10 = false,
  decision = null,
  issues = null,
  findings = null,
  onApplyFix = null,
  fixBusy = false,
}) {
  if (!packet) {
    return (
      <PanelShell stepLabel="01" icon={Stethoscope} title="Clinic" subtitle="Waiting for packet">
        <div className="flex-1 flex items-center justify-center text-center text-sm text-muted-foreground py-12">
          Select a scenario above to load the EDI 837 packet.
        </div>
      </PanelShell>
    )
  }

  const errorIssues = (issues || []).filter((i) => i.severity === 'error')
  const showAegisFeedback = decision?.status === 'rejected' && errorIssues.length > 0
  const total = packet.bill_items.reduce((s, i) => s + i.unit_price_eur * i.quantity, 0)

  return (
    <PanelShell stepLabel="01" icon={Stethoscope} title="Clinic" subtitle={packet.clinic_name}>
      {/* Patient block */}
      <div className="border-l-2 border-primary pl-3 mb-5">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5 mb-1">
          <UserRound size={11} /> Patient
        </div>
        <div className="font-semibold text-foreground">{packet.patient.full_name}</div>
        <div className="text-[11px] text-muted-foreground font-mono mt-0.5">
          {packet.patient.patient_id} · born {packet.patient.date_of_birth}
        </div>
      </div>

      {/* Doctor note */}
      <SectionLabel icon={FileText}>Doctor's note (free text)</SectionLabel>
      <div className="bg-secondary/60 rounded-xl p-4 border border-border text-sm leading-relaxed text-foreground/90 italic mb-5">
        "{packet.doctor_note}"
      </div>

      <SectionLabel icon={Paperclip}>Supporting documents</SectionLabel>
      <div className="bg-secondary/40 rounded-xl p-3 border border-border mb-5">
        {packet.supporting_documents?.length > 0 ? (
          <div className="flex gap-1.5 flex-wrap">
            {packet.supporting_documents.map((doc) => (
              <Badge key={doc} variant="outline" className="font-mono">
                {doc}
              </Badge>
            ))}
          </div>
        ) : (
          <div className="text-xs text-muted-foreground italic">
            No supporting documents attached.
          </div>
        )}
      </div>

      {/* Bill items */}
      <SectionLabel icon={Receipt}>Bill line items</SectionLabel>
      <div className="space-y-2 mb-4">
        <AnimatePresence>
          {packet.bill_items.map((item, idx) => (
            <motion.div
              key={item.cpt_code + idx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-card rounded-xl p-3 border border-border"
            >
              <div className="flex justify-between items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-[10px] text-accent font-bold tracking-wider">
                    CPT · {item.cpt_code}
                  </div>
                  <div className="text-sm font-semibold text-foreground mt-0.5">
                    {item.description}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-bold text-foreground font-mono tabular-nums">
                    {item.unit_price_eur.toFixed(2)} €
                  </div>
                  <div className="text-[10px] text-muted-foreground">× {item.quantity}</div>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-border/70 flex items-center gap-2 flex-wrap">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                  ICD-10
                </span>
                {item.icd10_codes.length === 0 ? (
                  highlightMissingIcd10 ? (
                    <Badge variant="danger" className="animate-pulse">
                      <AlertCircle size={10} /> MISSING
                    </Badge>
                  ) : (
                    <Badge variant="outline">MISSING</Badge>
                  )
                ) : (
                  item.icd10_codes.map((c) => (
                    <Badge key={c} variant="live" className="font-mono">
                      {c}
                    </Badge>
                  ))
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="pt-3 mt-auto border-t border-border flex justify-between items-center">
        <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
          {packet.packet_id}
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Total: </span>
          <span className="font-bold text-primary font-mono tabular-nums">
            {total.toFixed(2)} €
          </span>
        </div>
      </div>

      <AnimatePresence>
        {showAegisFeedback && (
          <AegisFeedback
            key="feedback"
            issues={errorIssues}
            findings={findings}
            onApply={onApplyFix}
            busy={fixBusy}
          />
        )}
      </AnimatePresence>
    </PanelShell>
  )
}

// ------------ Aegis feedback (error + apply) ------------

function AegisFeedback({ issues, findings, onApply, busy }) {
  const proposedFixes = issues.map((issue) => {
    let fix = issue.suggested_fix || {}
    if (
      (issue.issue_type === 'missing_icd10_justification' ||
        issue.issue_type === 'icd10_procedure_mismatch') &&
      (!fix.codes || fix.codes.length === 0) &&
      findings?.length > 0
    ) {
      fix = {
        action: 'add_icd10',
        to_cpt: issue.line_item_cpt,
        codes: findings.slice(0, 1).map((f) => f.suggested_icd10),
      }
    }
    return { issue, fix }
  })

  const applicableFixes = proposedFixes.filter((p) =>
    p.fix.action === 'add_icd10' || p.fix.action === 'attach_documents'
  )
  const canApply = applicableFixes.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      className="mt-5"
    >
      <Alert variant="destructive" className="border-2">
        <AlertTriangle className="h-5 w-5" />
        <AlertTitle>AEGIS returned the bill</AlertTitle>
        <AlertDescription>
          {issues.length} {issues.length === 1 ? 'error' : 'errors'} · bill not sent to insurance
        </AlertDescription>
      </Alert>

      <div className="space-y-2 mt-3">
        {proposedFixes.map(({ issue, fix }, idx) => (
          <div key={idx} className="bg-card rounded-xl border border-border p-3">
            <div className="flex items-start gap-3">
              <Badge variant="danger" className="rounded-full w-6 h-6 p-0 flex items-center justify-center text-[10px] shrink-0">
                {idx + 1}
              </Badge>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-foreground leading-snug">
                  {issue.explanation}
                </div>
                <div className="text-[10px] text-muted-foreground mt-1.5 font-mono uppercase tracking-wider">
                  CPT {issue.line_item_cpt} · {issue.issue_type.replace(/_/g, ' ')}
                </div>

                {fix.action === 'add_icd10' && fix.codes?.length > 0 && (
                  <Alert variant="accent" className="mt-2.5 p-2.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    <AlertTitle className="text-[10px] uppercase tracking-wider mb-1">
                      AI agent suggestion
                    </AlertTitle>
                    <AlertDescription className="text-xs text-foreground">
                      Add ICD-10{' '}
                      {fix.codes.map((c) => (
                        <Badge key={c} variant="live" className="font-mono mx-0.5">
                          {c}
                        </Badge>
                      ))}{' '}
                      to CPT <span className="font-mono font-semibold">{fix.to_cpt}</span>
                    </AlertDescription>
                  </Alert>
                )}

                {fix.action === 'remove_line' && (
                  <Alert variant="warning" className="mt-2.5 p-2.5">
                    <Trash2 className="h-3.5 w-3.5" />
                    <AlertTitle className="text-[10px] uppercase tracking-wider mb-1">
                      AI agent suggestion
                    </AlertTitle>
                    <AlertDescription className="text-xs text-foreground">
                      Remove line item <span className="font-mono font-semibold">CPT {fix.cpt}</span> from the bill
                    </AlertDescription>
                  </Alert>
                )}

                {fix.action === 'attach_documents' && fix.documents?.length > 0 && (
                  <Alert variant="accent" className="mt-2.5 p-2.5">
                    <Paperclip className="h-3.5 w-3.5" />
                    <AlertTitle className="text-[10px] uppercase tracking-wider mb-1">
                      Missing before submission
                    </AlertTitle>
                    <AlertDescription className="text-xs text-foreground">
                      Attach {formatList(fix.documents)} before sending this bill to insurance.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3">
        {canApply ? (
          <>
            <Button
              onClick={() => onApply?.(applicableFixes.map((p) => p.fix))}
              disabled={busy || !onApply}
              variant="accent"
              size="lg"
              className="w-full"
            >
              <Sparkles size={14} />
              {busy ? 'Applying fix...' : 'Apply fix to system'}
            </Button>
            <div className="text-[10px] text-muted-foreground text-center mt-2">
              After applying, click <span className="text-accent font-semibold">Run demo</span> to resubmit the corrected bill.
            </div>
          </>
        ) : (
          <PreAuthBlockedNote issues={issues} />
        )}
      </div>
    </motion.div>
  )
}

function PreAuthBlockedNote({ issues }) {
  const isPreAuth = (issues || []).some((i) => i.issue_type === 'contract_limit_violation')

  if (isPreAuth) {
    return (
      <Alert variant="warning">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Procedure must NOT be scheduled</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            Aegis stopped the request <span className="font-semibold">BEFORE</span> the procedure
            was performed. Notify the patient that insurance will not cover the MRI
            (a prior one was done less than 6 months ago).
          </p>
          <div>
            <div className="text-[10px] uppercase tracking-wider font-semibold mt-2 mb-1 opacity-80">
              Patient can choose
            </div>
            <ul className="text-[11px] space-y-0.5 list-disc list-inside">
              <li>Cancel the procedure</li>
              <li>Pay out of pocket (320 €)</li>
              <li>Submit additional documentation for exception</li>
            </ul>
          </div>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Alert variant="warning">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Manual intervention required</AlertTitle>
      <AlertDescription>
        This error cannot be automatically corrected. A physician must review the case
        and decide on next steps.
      </AlertDescription>
    </Alert>
  )
}

// ------------ helpers ------------

function formatList(items) {
  if (!items?.length) return ''
  if (items.length === 1) return items[0]
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`
}

function SectionLabel({ icon: Icon, children }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <Icon size={13} className="text-accent" strokeWidth={2.2} />
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
        {children}
      </span>
    </div>
  )
}
