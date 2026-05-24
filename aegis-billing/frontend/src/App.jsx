import { useEffect, useState, useCallback, useRef } from 'react'
import { ShieldCheck } from 'lucide-react'

import ClinicPanel from './components/ClinicPanel'
import ClearinghousePanel from './components/ClearinghousePanel'
import InsurancePanel from './components/InsurancePanel'
import PipelineAnimation from './components/PipelineAnimation'
import StatsDashboard from './components/StatsDashboard'
import NarratorOverlay from './components/NarratorOverlay'
import ScenarioSelector from './components/ScenarioSelector'

import {
  listScenarios, getScenario, streamIntercept, applyFix, recordStats, getStats, resetScenario,
} from './lib/api'

const STAGE_NARRATIVE = {
  clearinghouse_received: { text: 'EDI 837 packet entered clearinghouse', stepNumber: 1, pipeline: 'to_clearinghouse' },
  agent1_started: { text: 'Agent 1 reading the doctor\'s free text...', stepNumber: 2, pipeline: 'in_clearinghouse' },
  agent1_done: { text: 'Agent 1 extracted clinical findings and ICD-10 codes', stepNumber: 2, pipeline: 'in_clearinghouse' },
  agent2_started: { text: 'Agent 2 searching the insurance contract (Graph RAG)', stepNumber: 3, pipeline: 'in_clearinghouse' },
  agent2_done: { text: 'Agent 2 extracted rules from the contract', stepNumber: 3, pipeline: 'in_clearinghouse' },
  agent3_started: { text: 'Agent 3 cross-checking the bill...', stepNumber: 4, pipeline: 'in_clearinghouse' },
  agent3_done: { text: 'Agent 3 making the decision', stepNumber: 4, pipeline: 'in_clearinghouse' },
  delivered_to_insurance: { text: 'Bill delivered to insurance', stepNumber: 5, pipeline: 'to_insurance' },
  blocked_by_aegis: { text: 'STOP! Aegis blocked a poorly prepared bill.', stepNumber: 5, pipeline: 'blocked' },
}

export default function App() {
  const [scenarios, setScenarios] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [packet, setPacket] = useState(null)
  const [running, setRunning] = useState(false)

  const [agentStates, setAgentStates] = useState({ 1: 'idle', 2: 'idle', 3: 'idle' })
  const [agentResults, setAgentResults] = useState({ 1: null, 2: null, 3: null })
  const [decision, setDecision] = useState(null)

  const [narrator, setNarrator] = useState(null)
  const [pipelineStage, setPipelineStage] = useState('idle')

  const [fixBusy, setFixBusy] = useState(false)

  const [stats, setStats] = useState(null)
  const closeStreamRef = useRef(null)

  useEffect(() => {
    listScenarios().then(setScenarios).catch(console.error)
    getStats().then(setStats).catch(() => {})
  }, [])

  const handleSelect = useCallback(async (id) => {
    setSelectedId(id)
    setDecision(null)
    setAgentStates({ 1: 'idle', 2: 'idle', 3: 'idle' })
    setAgentResults({ 1: null, 2: null, 3: null })
    setPipelineStage('idle')
    setNarrator(null)
    try {
      // Reset previous fixes so the scenario starts from its initial broken state.
      await resetScenario(id).catch(() => {})
      const p = await getScenario(id)
      setPacket(p)
    } catch (e) { console.error(e) }
  }, [])

  const handleRun = useCallback(() => {
    if (!selectedId) return
    setRunning(true)
    setDecision(null)
    setAgentStates({ 1: 'idle', 2: 'idle', 3: 'idle' })
    setAgentResults({ 1: null, 2: null, 3: null })
    setPipelineStage('to_clearinghouse')
    setNarrator({ text: 'Starting demo...', stepNumber: 0 })

    closeStreamRef.current = streamIntercept(selectedId, {
      onStage: (data) => {
        const meta = STAGE_NARRATIVE[data.stage]
        if (meta) {
          setNarrator({ text: meta.text, stepNumber: meta.stepNumber })
          setPipelineStage(meta.pipeline)
        }
        if (data.stage === 'agent1_started') setAgentStates((s) => ({ ...s, 1: 'running' }))
        if (data.stage === 'agent1_done') setAgentStates((s) => ({ ...s, 1: 'done' }))
        if (data.stage === 'agent2_started') setAgentStates((s) => ({ ...s, 2: 'running' }))
        if (data.stage === 'agent2_done') setAgentStates((s) => ({ ...s, 2: 'done' }))
        if (data.stage === 'agent3_started') setAgentStates((s) => ({ ...s, 3: 'running' }))
      },
      onAgentResult: (data) => {
        const num = data.agent_number
        if (num === 1) setAgentResults((r) => ({ ...r, 1: data.findings }))
        else if (num === 2) setAgentResults((r) => ({ ...r, 2: data.rules }))
        else if (num === 3) {
          setAgentResults((r) => ({ ...r, 3: data.issues }))
          const hasErrors = (data.issues || []).some((i) => i.severity === 'error')
          setAgentStates((s) => ({ ...s, 3: hasErrors ? 'flagged' : 'done' }))
        }
      },
      onDecision: (data) => {
        setDecision(data)
        recordStats(data).then(setStats).catch(() => {})
      },
      onDone: () => {
        setRunning(false)
        closeStreamRef.current = null
      },
      onError: (e) => {
        console.error('SSE error', e)
        setRunning(false)
        setNarrator({
          text: 'Backend communication error. Check that the server is running.',
          stepNumber: 0,
        })
      },
    })
  }, [selectedId])

  const handleApplyFix = useCallback(async (fixes) => {
    if (!selectedId) return
    setFixBusy(true)
    try {
      // Backend applies fixes and returns the corrected packet. The audit does
      // not run yet; the user clicks Run again to see the pipeline pass.
      const fixedPacket = await applyFix(selectedId, fixes)
      setPacket(fixedPacket)

      // Reset agents and decision so the UI is ready for a new run.
      setDecision(null)
      setAgentStates({ 1: 'idle', 2: 'idle', 3: 'idle' })
      setAgentResults({ 1: null, 2: null, 3: null })
      setPipelineStage('idle')
      setNarrator({
        text: 'Fix applied to the bill. Click "Run" to resubmit.',
        stepNumber: 0,
      })
    } catch (e) {
      console.error(e)
    } finally {
      setFixBusy(false)
    }
  }, [selectedId])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Compact top bar: logo + scenarios + Run */}
      <header className="sticky top-0 z-30 bg-aegis-panel border-b border-aegis-border">
        <div className="max-w-[1440px] mx-auto px-6 py-3 flex items-center gap-6 flex-wrap">
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-lg bg-aegis-primary flex items-center justify-center">
              <ShieldCheck size={20} className="text-white" strokeWidth={2.2} />
            </div>
            <div>
              <div className="font-bold text-base text-aegis-primary tracking-tight leading-none">
                AegisBilling<span className="text-aegis-accent">.ai</span>
              </div>
              <div className="text-[10px] text-aegis-muted mt-0.5 leading-none uppercase tracking-wider font-semibold">
                AI clearinghouse filter
              </div>
            </div>
          </div>

          <ScenarioSelector
            scenarios={scenarios}
            selectedId={selectedId}
            onSelect={handleSelect}
            onRun={handleRun}
            running={running}
          />
        </div>
      </header>

      {/* Main demo area */}
      <main className="max-w-[1440px] w-full mx-auto px-6 py-6 flex-1 flex flex-col gap-5">
        <StatsDashboard stats={stats} />
        <PipelineAnimation activeStage={pipelineStage} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 flex-1 min-h-[600px]">
          <ClinicPanel
            packet={packet}
            highlightMissingIcd10={running && packet?.bill_items?.some((b) => b.icd10_codes.length === 0)}
            decision={decision}
            issues={agentResults[3]}
            findings={agentResults[1]}
            onApplyFix={handleApplyFix}
            fixBusy={fixBusy}
          />
          <ClearinghousePanel agentStates={agentStates} agentResults={agentResults} decision={decision} />
          <InsurancePanel packet={packet} decision={decision} />
        </div>
      </main>

      <NarratorOverlay step={narrator?.text} stepNumber={narrator?.stepNumber} />

      <footer className="border-t border-aegis-border bg-aegis-panel">
        <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3 text-[11px] text-aegis-muted">
          <div>
            © 2026 AegisBilling.ai · HIPAA & GDPR compliant · Multi-Agent + Graph RAG
          </div>
          <div>Python/FastAPI · React/Vite</div>
        </div>
      </footer>
    </div>
  )
}
