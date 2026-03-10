import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../components/ui/button'
import MicVisualizer from '../components/MicVisualizer'
import TimelapseForm from '../components/TimelapseForm'

type ApiResult = Record<string, any>

const API_BASE = import.meta.env.VITE_API_BASE || '' // same origin by default

export default function App() {
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [jsonOut, setJsonOut] = useState('')
  const [busy, setBusy] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [progress, setProgress] = useState(0)
  const progressTimer = useRef<number | null>(null)
  const [pendingUrl, setPendingUrl] = useState<string | null>(null)
  const startTsRef = useRef<number>(0)
  const expectedMsRef = useRef<number>(120_000)
  const clipCountRef = useRef<number>(0)
  const [clips, setClips] = useState<any[]>([])
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement | null>(null)
  const [loginRequired, setLoginRequired] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [stitchConfirmOpen, setStitchConfirmOpen] = useState(false)
  const [pendingAudio, setPendingAudio] = useState<File | null>(null)
  const [pendingTranscript, setPendingTranscript] = useState<string>('')
  const [auth, setAuth] = useState<{ authenticated: boolean; user?: any; usage_count: number; limit: number } | null>(null)
  const [mode, setMode] = useState<'speech' | 'timelapse'>('timelapse')
  const [stepByStep, setStepByStep] = useState(false)
  const [pipelineState, setPipelineState] = useState<Record<string, any> | null>(null)
  const [phaseCompleted, setPhaseCompleted] = useState<string | null>(null)
  const [pipelineError, setPipelineError] = useState<string | null>(null)
  const [formPayload, setFormPayload] = useState<Record<string, any> | null>(null)

  const canRecord = useMemo(() => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia), [])
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recording, setRecording] = useState(false)
  const recordedChunks = useRef<Blob[]>([])
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(null)

  const wakeLockRef = useRef<WakeLockSentinel | null>(null)

  useEffect(() => {
    async function toggleWakeLock() {
      if (busy) {
        try {
          if ('wakeLock' in navigator) {
            wakeLockRef.current = await navigator.wakeLock.request('screen')
          }
        } catch { /* browser may deny */ }
      } else {
        try { await wakeLockRef.current?.release() } catch {}
        wakeLockRef.current = null
      }
    }
    toggleWakeLock()
    return () => { try { wakeLockRef.current?.release() } catch {} }
  }, [busy])

  useEffect(() => {
    fetch(`${API_BASE}/api/clips`).then(r => r.json()).then((list) => { setClips(list); clipCountRef.current = Array.isArray(list) ? list.length : 0 }).catch(() => setClips([]))
    fetchSession()
  }, [])

  useEffect(() => { clipCountRef.current = clips.length }, [clips])

  function clearProgressTimer() {
    if (progressTimer.current) {
      window.clearInterval(progressTimer.current)
      progressTimer.current = null
    }
  }

  function beginProgress(message: string, expectedMs: number) {
    setStatusMsg(message)
    setProgress(0)
    startTsRef.current = performance.now()
    expectedMsRef.current = expectedMs
    clearProgressTimer()
    // Continuously move from 0 to ~99.5% over expectedMs
    progressTimer.current = window.setInterval(() => {
      const elapsed = performance.now() - startTsRef.current
      const ratio = Math.min(elapsed / expectedMsRef.current, 0.995)
      setProgress(ratio * 100)
    }, 120)
  }

  function endProgress(finalMessage?: string) {
    clearProgressTimer()
    setProgress(100)
    if (finalMessage) setStatusMsg(finalMessage)
    window.setTimeout(() => {
      setStatusMsg('')
      setProgress(0)
    }, 1200)
  }

  async function preloadVideo(url: string, timeoutMs = 60000): Promise<void> {
    return new Promise((resolve, reject) => {
      const v = document.createElement('video')
      v.preload = 'auto'
      v.src = url
      let done = false
      const cleanup = () => {
        v.removeAttribute('src')
        try { v.load() } catch (_) {}
      }
      const onReady = () => {
        if (done) return
        done = true
        cleanup()
        resolve()
      }
      const onError = () => {
        if (done) return
        done = true
        cleanup()
        reject(new Error('Video failed to load'))
      }
      v.addEventListener('canplaythrough', onReady, { once: true })
      v.addEventListener('loadeddata', onReady, { once: true })
      v.addEventListener('canplay', onReady, { once: true })
      v.addEventListener('error', onError, { once: true })
      const to = window.setTimeout(() => {
        onError()
      }, timeoutMs)
      // Also resolve on loadedmetadata if others don't fire
      v.addEventListener('loadedmetadata', () => {
        if (!done) {
          window.clearTimeout(to)
          onReady()
        }
      }, { once: true })
    })
  }

  async function preloadWithFallback(url: string, fallbackMs: number): Promise<void> {
    return Promise.race([
      preloadVideo(url),
      new Promise<void>((resolve) => setTimeout(() => resolve(), fallbackMs)),
    ])
  }

  // Removed prompt generation

  async function handleSpeechToVideo(file: File) {
    setBusy(true)
    try {
      // 2 minutes target for generation via audio
      beginProgress('Processing audio…', 120_000)
      const body = new FormData()
      body.set('audio', file)
      let resp: Response
      try {
        resp = await fetch(`${API_BASE}/api/ads/superbowl`, { method: 'POST', body })
      } catch (e) {
        // Network error or server restarted mid-request
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      if (resp.status === 401) {
        setLoginRequired(true)
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Sign in required to continue.')
        setBusy(false)
        return
      }
      let data: ApiResult
      try {
        data = await resp.json()
      } catch {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      setJsonOut(JSON.stringify(data, null, 2))
      const url = data.video_url as string | undefined
      if (url) {
        setStatusMsg('Preparing video…')
        // Use the provider-returned media URL directly (no proxy)
        setPendingUrl(url)
        await preloadWithFallback(url, 15000)
        const elapsed = performance.now() - startTsRef.current
        const finish = () => {
          setVideoUrl(url)
          setPendingUrl(null)
          endProgress('Ready')
          // Refresh session usage so gating reflects the consumed free attempt
          ;(async () => { try { await fetchSession() } catch {} })()
        }
        const remaining = Math.max(0, expectedMsRef.current - elapsed)
        if (remaining > 0) {
          window.setTimeout(finish, remaining)
        } else {
          finish()
        }
      } else {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('No video URL returned')
      }
    } finally {
      setBusy(false)
    }
  }

  async function handlePromptToAd(promptText: string) {
    setBusy(true)
    try {
      // 2 minutes target for generation via text
      beginProgress('Processing prompt…', 120_000)
      const body = new FormData()
      body.set('prompt', promptText)
      let resp: Response
      try {
        resp = await fetch(`${API_BASE}/api/ads/superbowl`, { method: 'POST', body })
      } catch (e) {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      if (resp.status === 401) {
        setLoginRequired(true)
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Sign in required to continue.')
        setBusy(false)
        return
      }
      let data: ApiResult
      try {
        data = await resp.json()
      } catch {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      setJsonOut(JSON.stringify(data, null, 2))
      const raw = data.video_url as string | undefined
      if (raw) {
        // Support relative stitched URL with cache-buster
        const url = /^https?:/i.test(raw) ? raw : `${API_BASE}${raw}${raw.includes('?') ? '&' : '?'}t=${Date.now()}`
        setStatusMsg('Preparing video…')
        setPendingUrl(url)
        await preloadWithFallback(url, 15000)
        const elapsed = performance.now() - startTsRef.current
        const finish = () => {
          setVideoUrl(url)
          setPendingUrl(null)
          endProgress('Ready')
          ;(async () => { try { await fetchSession() } catch {} })()
        }
        const remaining = Math.max(0, expectedMsRef.current - elapsed)
        if (remaining > 0) {
          window.setTimeout(finish, remaining)
        } else {
          finish()
        }
      } else {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('No video URL returned')
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveLastClip(note?: string) {
    if (!videoUrl) return
    const body = new FormData()
    body.set('url', videoUrl)
    if (note) body.set('note', note)
    if (jsonOut) body.set('json_response', jsonOut)
    await fetch(`${API_BASE}/api/clips`, { method: 'POST', body })
    const list = await fetch(`${API_BASE}/api/clips`).then(r => r.json())
    setClips(list)
  }

  async function saveClipDirect(url: string, note?: string) {
    const body = new FormData()
    body.set('url', url)
    if (note) body.set('note', note)
    await fetch(`${API_BASE}/api/clips`, { method: 'POST', body })
    const list = await fetch(`${API_BASE}/api/clips`).then(r => r.json())
    setClips(list)
  }

  async function handleClearClips() {
    await fetch(`${API_BASE}/api/clips`, { method: 'DELETE' })
    const list = await fetch(`${API_BASE}/api/clips`).then(r => r.json())
    setClips(list)
  }

  async function handleStitchSaved() {
    setBusy(true)
    try {
      // 45 seconds per 2 clips (ceil)
      const clipsCount = clipCountRef.current > 0 ? clipCountRef.current : clips.length
      const stitchExpected = 45_000 * Math.max(1, Math.ceil(clipsCount / 2))
      beginProgress('Stitching saved clips…', stitchExpected)
      const body = new FormData()
      body.set('use_saved', 'true')
      let resp: Response
      try {
        resp = await fetch(`${API_BASE}/api/stitch`, { method: 'POST', body })
      } catch (e) {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      if (resp.status === 401) {
        setLoginRequired(true)
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Sign in required to continue.')
        setBusy(false)
        return
      }
      let data: ApiResult
      try {
        data = await resp.json()
      } catch {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Server restarted. Please retry.')
        return
      }
      setJsonOut(JSON.stringify(data, null, 2))
      if (data.success) {
        const stitched = (data.stitched_url as string) || ''
        const url = stitched || `${API_BASE}/api/stitched`
        setStatusMsg('Preparing video…')
        // No need to proxy local stitched file; use as is
        setPendingUrl(url)
        await preloadWithFallback(url, 15000)
        const elapsed = performance.now() - startTsRef.current
        const finish = () => {
          setVideoUrl(url)
          setPendingUrl(null)
          endProgress('Stitching complete')
          // Save stitched video into the LIST automatically (best-effort). Backend prunes old stitched entries.
          ;(async () => {
            try {
              await saveClipDirect(url, 'Stitched')
              const list = await fetch(`${API_BASE}/api/clips`).then(r => r.json())
              setClips(list)
            } catch {}
          })()
        }
        const remaining = Math.max(0, expectedMsRef.current - elapsed)
        if (remaining > 0) {
          window.setTimeout(finish, remaining)
        } else {
          finish()
        }
      } else {
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Stitching failed')
      }
    } finally {
      setBusy(false)
    }
  }

  function openStitchConfirm() {
    setStitchConfirmOpen(true)
  }

  function cancelStitchConfirm() {
    setStitchConfirmOpen(false)
  }

  async function proceedStitchConfirm() {
    setStitchConfirmOpen(false)
    await handleStitchSaved()
  }

  function signIn() {
    window.location.href = `${API_BASE}/api/auth/login`
  }

  async function signOut() {
    try { await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST' }) } catch {}
    await fetchSession()
  }

  async function fetchSession() {
    try {
      const r = await fetch(`${API_BASE}/api/auth/session`)
      const j = await r.json()
      setAuth({ authenticated: !!j?.authenticated, user: j?.user, usage_count: Number(j?.usage_count || 0), limit: Number(j?.limit || 0) })
      if (j?.authenticated) setLoginRequired(false)
    } catch {
      setAuth(null)
    }
  }

  async function confirmProceed() {
    const f = pendingAudio
    setConfirmOpen(false)
    if (pendingTranscript && pendingTranscript.trim().length > 0) {
      setPendingAudio(null)
      await handlePromptToAd(pendingTranscript.trim())
    } else if (f) {
      setPendingAudio(null)
      await handleSpeechToVideo(f)
    }
  }

  function confirmCancel() {
    setPendingAudio(null)
    setPendingTranscript('')
    setConfirmOpen(false)
    setStatusMsg('')
  }

  async function startRecording() {
    if (!canRecord) return
    // Gate unauthenticated returning users client-side before accessing mic
    if (!auth?.authenticated && Number(auth?.usage_count || 0) >= Number(auth?.limit || 1)) {
      setLoginRequired(true)
      setStatusMsg('Sign in required to continue.')
      return
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const rec = new MediaRecorder(stream)
    recordedChunks.current = []
    setRecordingStream(stream)
    rec.ondataavailable = (e) => { if (e.data.size > 0) recordedChunks.current.push(e.data) }
    rec.onstop = async () => {
      const blob = new Blob(recordedChunks.current, { type: 'audio/webm' })
      const file = new File([blob], 'recording.webm', { type: 'audio/webm' })
      // Defer submission until user confirms in-app, and open modal immediately
      setPendingAudio(file)
      setPendingTranscript('')
      setConfirmOpen(true)
      // Kick off transcription in the background; update when done
      ;(async () => {
        try {
          const fd = new FormData()
          fd.set('audio', file)
          const r = await fetch(`${API_BASE}/api/transcribe`, { method: 'POST', body: fd })
          const j = await r.json()
          if (j?.success && j?.text) setPendingTranscript(String(j.text))
        } catch {
          // ignore; leave transcript blank
        }
      })()
    }
    rec.start()
    setMediaRecorder(rec)
    setRecording(true)
  }

  function stopRecording() {
    mediaRecorder?.stop()
    setRecording(false)
    try {
      recordingStream?.getTracks()?.forEach(t => t.stop())
    } catch (_) {}
    setRecordingStream(null)
  }

  const NUM_STAGES = 7
  const STAGE_PHASES = Array.from({ length: NUM_STAGES }, (_, i) => `stage_${i + 1}`)
  const PHASE_ORDER = ['plan', ...STAGE_PHASES, 'videos'] as const
  const PHASE_LABELS: Record<string, string> = {
    plan: 'Scene Bible + Stage 1 Plan',
    ...Object.fromEntries(STAGE_PHASES.map((p, i) => [p, `Stage ${i + 1} Image`])),
    videos: 'Video Transitions (Seedance)',
    stitch: 'Stitching',
    done: 'Stitching',
  }

  function nextStopAfter(currentPhase: string | null): string | null {
    if (!currentPhase) return 'plan'
    const idx = PHASE_ORDER.indexOf(currentPhase as any)
    if (idx < 0 || idx >= PHASE_ORDER.length - 1) return null
    return PHASE_ORDER[idx + 1]
  }

  function detectLastCompletedPhase(state: Record<string, any>): string | null {
    if (state.transition_videos?.length) return 'videos'
    const nImages = state.keyframe_images?.length ?? 0
    if (nImages > 0) return `stage_${nImages}`
    if (state.scene_bible) return 'plan'
    return null
  }

  const POLL_INTERVALS: Record<string, number> = {
    plan: 2000,
    stage: 3000,
    videos: 5000,
    stitch: 30000,
  }
  const DEFAULT_POLL_INTERVAL = 3000
  const MAX_NETWORK_FAILS = 10

  function calcProgress(phase: string | null, step: number, total: number, stopAfter: string | null): number {
    if (!phase || total <= 0) return 0
    const phaseRatio = step / total
    if (stopAfter) return Math.min(phaseRatio * 100, 99.5)
    const stageMatch = phase.match(/^stage_(\d+)$/)
    if (stageMatch) {
      const stageNum = parseInt(stageMatch[1], 10)
      const stageStart = 3 + ((stageNum - 1) / NUM_STAGES) * 47
      const stageEnd = 3 + (stageNum / NUM_STAGES) * 47
      return Math.min(stageStart + (stageEnd - stageStart) * phaseRatio, 99.5)
    }
    const ranges: Record<string, [number, number]> = {
      plan: [0, 3], videos: [50, 95], stitch: [95, 100],
    }
    const range = ranges[phase]
    if (!range) return 0
    const [start, end] = range
    return Math.min(start + (end - start) * phaseRatio, 99.5)
  }

  function extractPartial(data: Record<string, any>): Record<string, any> | null {
    if (!data.scene_bible && !data.keyframe_images && !data.transition_videos) return null
    const p: Record<string, any> = {}
    if (data.scene_bible) p.scene_bible = data.scene_bible
    if (data.crew) p.crew = data.crew
    if (data.elements) p.elements = data.elements
    if (data.renovated_elements) p.renovated_elements = data.renovated_elements
    if (data.stages) p.stages = data.stages
    if (data.seed) p.seed = data.seed
    if (data.keyframe_images) p.keyframe_images = data.keyframe_images
    if (data.transition_videos) p.transition_videos = data.transition_videos
    return p
  }

  async function runPipeline(payload: Record<string, any>, stopAfter: string | null, resumeState: Record<string, any> | null) {
    if (!auth?.authenticated && Number(auth?.usage_count || 0) >= Number(auth?.limit || 1)) {
      setLoginRequired(true)
      setStatusMsg('Sign in required to continue.')
      return
    }
    setBusy(true)
    setPipelineError(null)
    setPhaseCompleted(null)

    try {
      setStatusMsg('Starting...')
      setProgress(0)

      const body: Record<string, any> = { ...payload }
      if (stopAfter) body.stop_after = stopAfter
      if (resumeState) body.resume_state = resumeState

      // 1. Start the job
      let startResp: Response
      try {
        startResp = await fetch(`${API_BASE}/api/generate/timelapse`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
      } catch {
        setStatusMsg('Network error — could not reach server.')
        if (resumeState) {
          setPipelineState(resumeState)
          setPipelineError('Network error — could not reach server. Your previous progress is preserved — click Resume to retry.')
        }
        return
      }

      if (startResp.status === 401) {
        setLoginRequired(true)
        setStatusMsg('Sign in required to continue.')
        return
      }

      let startData: Record<string, any>
      try {
        startData = await startResp.json()
      } catch {
        setStatusMsg('Server returned an invalid response.')
        if (resumeState) {
          setPipelineState(resumeState)
          setPipelineError('Server returned an invalid response. Your previous progress is preserved — click Resume to retry.')
        }
        return
      }

      const jobId = startData.job_id as string | undefined
      if (!jobId) {
        setStatusMsg('Server did not return a job ID.')
        return
      }

      // 2. Poll for status — adaptive interval per phase
      let lastPartial: Record<string, any> | null = resumeState
      let networkFailCount = 0
      let result: Record<string, any> | null = null
      let currentPhase: string | null = null

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const phaseKey = currentPhase?.startsWith('stage_') ? 'stage' : (currentPhase ?? '')
        const interval = POLL_INTERVALS[phaseKey] ?? DEFAULT_POLL_INTERVAL
        await new Promise(r => setTimeout(r, interval))

        let jobData: Record<string, any>
        try {
          const r = await fetch(`${API_BASE}/api/jobs/${jobId}`)
          if (r.status === 404) {
            const errMsg = 'Server restarted — job was lost.'
            setStatusMsg(errMsg)
            setProgress(0)
            if (lastPartial) {
              setPipelineState(lastPartial)
              setPipelineError(errMsg + ' Your previous progress is preserved — click Resume to retry.')
            }
            return
          }
          jobData = await r.json()
          networkFailCount = 0
        } catch {
          networkFailCount++
          if (networkFailCount >= MAX_NETWORK_FAILS) {
            const errMsg = 'Lost connection to server.'
            setStatusMsg(errMsg)
            setProgress(0)
            if (lastPartial) {
              setPipelineState(lastPartial)
              setPipelineError(errMsg + ' Your previous progress is preserved — click Resume to retry.')
            }
            return
          }
          continue
        }

        if (jobData.partial_result) lastPartial = jobData.partial_result
        currentPhase = (jobData.phase as string) || currentPhase

        const msg = (jobData.message as string) || 'Processing...'
        setStatusMsg(msg)
        setProgress(calcProgress(jobData.phase, jobData.step ?? 0, jobData.total_steps ?? 0, stopAfter))

        if (jobData.status === 'completed' || jobData.status === 'failed') {
          result = jobData.result as Record<string, any> | null
          break
        }
      }

      // 3. Process result
      if (!result) {
        setStatusMsg('No result returned from server.')
        setProgress(0)
        return
      }

      setJsonOut(JSON.stringify(result, null, 2))

      if (!result.success) {
        setProgress(0)
        const errMsg = result.error
          ? `Error: ${typeof result.error === 'string' ? result.error : 'Generation failed'}`
          : 'Generation failed'
        setStatusMsg(errMsg)

        const partial = extractPartial(result) || lastPartial
        if (partial) {
          setPipelineState(partial)
          setPipelineError(errMsg)
        }
        return
      }

      const completed = result.phase_completed as string | undefined
      if (completed && completed !== 'done') {
        const accumulated = extractPartial(result)
        if (accumulated) setPipelineState(accumulated)
        setPhaseCompleted(completed)
        setProgress(100)
        setStatusMsg(`Phase complete: ${PHASE_LABELS[completed] || completed}`)
        setTimeout(() => { setStatusMsg(''); setProgress(0) }, 1200)
        return
      }

      const raw = result.video_url as string | undefined
      if (raw) {
        const url = /^https?:/i.test(raw) ? raw : `${API_BASE}${raw}${raw.includes('?') ? '&' : '?'}t=${Date.now()}`
        setStatusMsg('Preparing video...')
        setPendingUrl(url)
        await preloadWithFallback(url, 15000)
        setVideoUrl(url)
        setPendingUrl(null)
        setProgress(100)
        setStatusMsg('Ready')
        setPipelineState(null)
        setPhaseCompleted(null)
        setTimeout(() => { setStatusMsg(''); setProgress(0) }, 1200)
        ;(async () => { try { await fetchSession() } catch {} })()
      } else {
        setProgress(0)
        setStatusMsg('No video URL returned')
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleTimelapseSubmit(payload: Record<string, any>) {
    setFormPayload(payload)
    setPipelineState(null)
    setPhaseCompleted(null)
    setPipelineError(null)
    setVideoUrl(null)
    if (stepByStep) {
      await runPipeline(payload, 'plan', null)
    } else {
      await runPipeline(payload, null, null)
    }
  }

  async function handleContinuePipeline() {
    if (!formPayload || !pipelineState || !phaseCompleted) return
    const stop = nextStopAfter(phaseCompleted)
    setPipelineError(null)
    await runPipeline(formPayload, stop, pipelineState)
  }

  async function handleResumePipeline() {
    if (!formPayload || !pipelineState) return
    setPipelineError(null)
    setStatusMsg('Resuming from where it left off...')
    const stop = stepByStep ? nextStopAfter(detectLastCompletedPhase(pipelineState)) : null
    await runPipeline(formPayload, stop, pipelineState)
  }

  function handleStopPipeline() {
    const label = phaseCompleted ? (PHASE_LABELS[phaseCompleted] || phaseCompleted) : ''
    setPhaseCompleted(null)
    setFormPayload(null)
    setPipelineError(null)
    setStatusMsg(label ? `Pipeline stopped after ${label}.` : 'Pipeline stopped.')
  }

  function handleStartOver() {
    setPipelineState(null)
    setPhaseCompleted(null)
    setPipelineError(null)
    setFormPayload(null)
    setVideoUrl(null)
    setJsonOut('')
    setStatusMsg('')
    setProgress(0)
  }

  return (
    <div className="min-h-dvh bg-background">
      <header className="border-b">
        <div className="container py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold">
            {mode === 'timelapse' ? 'Interior Timelapse' : 'Speech to Video'}
          </h1>
          <div className="flex items-center gap-2">
            {auth?.authenticated && <span className="text-xs text-muted-foreground">Signed in as {auth?.user?.email || 'user'}</span>}
            <Button variant="outline" onClick={auth?.authenticated ? signOut : signIn}>{auth?.authenticated ? 'Sign out' : 'Sign in'}</Button>
          </div>
        </div>
        <div className="container pb-3">
          <div className="inline-flex rounded-md border bg-muted p-0.5">
            <button
              onClick={() => setMode('timelapse')}
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${mode === 'timelapse' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Interior Timelapse
            </button>
            <button
              onClick={() => setMode('speech')}
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${mode === 'speech' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Speech to Video
            </button>
          </div>
        </div>
      </header>

      <main className="container py-8 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-8">
        {confirmOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="w-full max-w-md rounded-md border bg-card p-5 shadow">
              <h2 className="text-base font-semibold">Submit recording?</h2>
              <p className="mt-2 text-sm text-muted-foreground">{pendingTranscript ? 'Proceed to generate a video from your recorded audio?' : 'Just a sec. Generating transcript for confirmation...'}</p>
              <div className="mt-3">
                <textarea
                  className="w-full rounded border bg-background p-2 text-xs leading-5 max-h-40 min-h-[96px] outline-none"
                  placeholder={pendingTranscript ? '' : 'Type or wait for transcript…'}
                  value={pendingTranscript}
                  onChange={(e) => setPendingTranscript(e.target.value)}
                />
              </div>
              <div className="mt-4 flex justify-end gap-2">
                <Button variant="ghost" onClick={confirmCancel}>Cancel</Button>
                <Button onClick={confirmProceed}>Proceed</Button>
              </div>
            </div>
          </div>
        )}
        {stitchConfirmOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="w-full max-w-md rounded-md border bg-card p-5 shadow">
              <h2 className="text-base font-semibold">Stitch saved clips?</h2>
              <p className="mt-2 text-sm text-muted-foreground">This will stitch the saved clips in the order shown.</p>
              <div className="mt-4 flex justify-end gap-2">
                <Button variant="ghost" onClick={cancelStitchConfirm}>Cancel</Button>
                <Button onClick={proceedStitchConfirm}>Proceed</Button>
              </div>
            </div>
          </div>
        )}
        {(busy || statusMsg) && (
          <div>
            <div className="rounded-md border bg-card p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">{statusMsg || 'Processing…'}</span>
                <span className="text-xs text-muted-foreground">{Math.round(progress)}%</span>
              </div>
              <div className="mt-2 h-2 w-full rounded bg-muted">
                <div className="h-2 rounded bg-primary" style={{ width: `${Math.max(0, Math.min(progress, 100))}%`, transition: 'width 160ms linear' }} />
              </div>
            </div>
          </div>
        )}
        {phaseCompleted && pipelineState && !busy && (
          <div className="rounded-md border bg-card p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">
                Phase complete: {PHASE_LABELS[phaseCompleted] || phaseCompleted}
              </h3>
              <div className="flex items-center gap-1">
                {PHASE_ORDER.map((p, i) => (
                  <div
                    key={p}
                    className={`h-2 rounded-full ${
                      PHASE_ORDER.indexOf(phaseCompleted as any) >= i
                        ? 'bg-primary'
                        : 'bg-muted'
                    } ${p.startsWith('stage_') ? 'w-4' : 'w-6'}`}
                    title={PHASE_LABELS[p]}
                  />
                ))}
              </div>
            </div>

            {phaseCompleted === 'plan' && pipelineState.stages && (
              <div className="space-y-3">
                <div>
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Scene Bible</span>
                  <p className="mt-1 text-sm bg-muted rounded p-2">{pipelineState.scene_bible}</p>
                </div>
                {pipelineState.crew && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Crew (3 Workers)</span>
                    <p className="mt-1 text-sm bg-muted rounded p-2">{pipelineState.crew}</p>
                  </div>
                )}
                {pipelineState.elements?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Elements to Renovate ({pipelineState.elements.length})
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {pipelineState.elements.map((e: string, i: number) => (
                        <span key={i} className="inline-block rounded-full bg-muted px-2.5 py-0.5 text-xs">
                          {e}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Stage 1 Description</span>
                  <p className="mt-1 text-sm bg-muted rounded p-2">{pipelineState.stages[0]?.description}</p>
                </div>
              </div>
            )}

            {phaseCompleted?.startsWith('stage_') && pipelineState.keyframe_images && (
              <div className="space-y-3">
                {pipelineState.elements?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Renovation Progress
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {pipelineState.elements.map((e: string, i: number) => {
                        const done = (pipelineState.renovated_elements || []).includes(e)
                        return (
                          <span key={i} className={`inline-block rounded-full px-2.5 py-0.5 text-xs ${done ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                            {done ? '✓ ' : ''}{e}
                          </span>
                        )
                      })}
                    </div>
                  </div>
                )}
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Keyframe Images ({pipelineState.keyframe_images.length} of {NUM_STAGES})
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {pipelineState.keyframe_images.map((kf: any, i: number) => (
                    <div key={i} className="space-y-1">
                      <img
                        src={kf.image_url}
                        alt={`Stage ${kf.stage}`}
                        className="w-full rounded border aspect-video object-cover"
                      />
                      <div className="text-xs text-center text-muted-foreground truncate" title={kf.description}>
                        Stage {kf.stage}
                      </div>
                    </div>
                  ))}
                </div>
                {pipelineState.stages && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Stage Descriptions</span>
                    {pipelineState.stages.map((s: any, i: number) => (
                      <div key={i} className="rounded bg-muted p-2">
                        <div className="text-xs font-medium">
                          {i === 0 ? 'Stage 1 — Starting State' : `Stage ${i + 1} — ${i === 1 ? 'Cleanup' : 'Edit'}`}
                          {s.renovated_element?.length > 0 && (
                            <span className="ml-1.5 text-primary">({s.renovated_element.join(', ')})</span>
                          )}
                        </div>
                        <div className="text-sm">{s.description || s.edit_delta}</div>
                        {s.transition_prompt && (
                          <div className="text-xs text-muted-foreground mt-0.5">
                            Transition: {s.transition_prompt}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {phaseCompleted === 'videos' && pipelineState.transition_videos && (
              <div className="space-y-3">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Transition Videos ({pipelineState.transition_videos.length})
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {pipelineState.transition_videos.map((url: string, i: number) => (
                    <div key={i} className="space-y-1">
                      <video
                        src={url}
                        className="w-full rounded border aspect-video object-cover"
                        controls
                        preload="metadata"
                        muted
                        playsInline
                      />
                      <div className="text-xs text-center text-muted-foreground">
                        Transition {i + 1} &rarr; {i + 2}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button onClick={handleContinuePipeline} disabled={busy}>
                {nextStopAfter(phaseCompleted)
                  ? `Continue to ${PHASE_LABELS[nextStopAfter(phaseCompleted)!] || 'next phase'}`
                  : 'Finish & Stitch'}
              </Button>
              <Button variant="secondary" onClick={handleStopPipeline} disabled={busy}>
                Stop
              </Button>
              <Button variant="outline" onClick={handleStartOver} disabled={busy}>
                Start Over
              </Button>
            </div>
          </div>
        )}

        {pipelineError && pipelineState && !phaseCompleted && !busy && (
          <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4 space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-destructive">Pipeline failed</h3>
              <p className="text-sm text-muted-foreground mt-1">{pipelineError}</p>
            </div>
            <div className="text-xs text-muted-foreground space-y-0.5">
              {pipelineState.scene_bible && <div>Plan: saved</div>}
              {pipelineState.keyframe_images && (
                <div>Images: {pipelineState.keyframe_images.length} generated</div>
              )}
              {pipelineState.transition_videos && (
                <div>
                  Videos: {pipelineState.transition_videos.length} of{' '}
                  {(pipelineState.keyframe_images?.length || 1) - 1} transitions done
                </div>
              )}
            </div>
            <div className="flex gap-2 pt-1">
              <Button onClick={handleResumePipeline} disabled={busy}>
                Resume from where it failed
              </Button>
              <Button variant="outline" onClick={handleStartOver} disabled={busy}>
                Start Over
              </Button>
            </div>
          </div>
        )}

        <section className="space-y-3">
          {mode === 'timelapse' ? (
            <TimelapseForm busy={busy} onSubmit={handleTimelapseSubmit} stepByStep={stepByStep} onStepByStepChange={setStepByStep} />
          ) : (
            <>
              {canRecord && (
                recording ? (
                  <Button className="w-full h-12" variant="destructive" onClick={stopRecording}>Stop Recording</Button>
                ) : (
                  <Button className="w-full h-12" onClick={startRecording} disabled={busy}>Record</Button>
                )
              )}
              {!recording && loginRequired && (
                <div className="text-xs text-destructive">Sign in required. Click the Sign in button above to continue.</div>
              )}
              {recording && (
                <div className="mt-2">
                  <MicVisualizer stream={recordingStream} />
                </div>
              )}
            </>
          )}
        </section>

        <section className="space-y-4">
          <div className="flex justify-center">
            <div className="aspect-video w-full max-w-3xl rounded-md border bg-black/50 flex items-center justify-center">
              {videoUrl ? (
                <video key={videoUrl} src={videoUrl} className="w-full h-full" controls onError={() => setStatusMsg('Video failed to load')} />
              ) : (
                <span className="text-sm text-muted-foreground">Your video will appear here</span>
              )}
            </div>
          </div>
          <div className="flex justify-center gap-2">
            <Button variant="outline" disabled={!videoUrl} onClick={() => handleSaveLastClip('')}>Save last clip</Button>
            <Button variant="outline" onClick={openStitchConfirm} disabled={busy}>Stitch saved clips</Button>
            <Button variant="outline" onClick={handleClearClips}>Clear clips</Button>
          </div>
        </section>

        <section className="max-w-3xl mx-auto space-y-2">
          <label className="text-sm font-medium">Result JSON</label>
          <pre className="min-h-40 max-h-80 overflow-auto rounded-md border bg-muted p-3 text-xs">
            {jsonOut || '{\n  "result": null\n}'}
          </pre>
        </section>
        </div>

        <aside className="hidden lg:block">
          <div className="sticky top-4 rounded-md border bg-card p-3 h-[calc(100vh-6rem)] overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold">LIST</span>
              <span className="text-xs text-muted-foreground">{clips.length}</span>
            </div>
            <div className="space-y-1">
              {clips.map((c, idx) => (
                <div
                  key={c.ts || idx}
                  className={`group w-full text-left grid grid-cols-[112px_1fr_auto] gap-3 p-2 rounded transition-transform ${dragIndex===idx ? 'bg-accent' : 'hover:bg-accent focus-within:bg-accent'} hover:scale-[1.02] focus-within:scale-[1.02] cursor-move`}
                  draggable
                  onDragStart={(e) => {
                    try { e.dataTransfer.setData('text/plain', String(idx)) } catch {}
                    try { e.dataTransfer.effectAllowed = 'move' } catch {}
                    setDragIndex(idx)
                  }}
                  onDragEnd={() => setDragIndex(null)}
                  onDragOver={(e) => { e.preventDefault() }}
                  onDrop={async (e) => {
                    e.preventDefault()
                    if (dragIndex===null || dragIndex===idx) return
                    const newList = [...clips]
                    const [moved] = newList.splice(dragIndex, 1)
                    newList.splice(idx, 0, moved)
                    setClips(newList)
                    setDragIndex(null)
                    try {
                      const order = newList.map(x => x.ts).filter(Boolean).join(',')
                      const fd = new FormData()
                      fd.set('order', order)
                      await fetch(`${API_BASE}/api/clips/reorder`, { method: 'POST', body: fd, credentials: 'include' })
                    } catch {}
                  }}
                >
                  <button onClick={() => setVideoUrl(c.url)} className="col-span-2 grid grid-cols-[112px_1fr] items-center gap-3 w-full text-left" draggable={false}>
                    <video
                      src={c.url}
                      className="w-28 h-16 rounded bg-black object-cover"
                      preload="metadata"
                      muted
                      playsInline
                      draggable={false}
                    />
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{(c.note || '').trim() || `Clip ${idx + 1}`}</div>
                      <div className="truncate text-xs text-muted-foreground">{c.url}</div>
                    </div>
                  </button>
                  <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
                    {c.has_response && (
                      <button
                        aria-label="View JSON response"
                        title="View JSON response"
                        onClick={async (e) => {
                          e.stopPropagation()
                          if (!c.ts) return
                          try {
                            const r = await fetch(`${API_BASE}/api/clips/${c.ts}/response`)
                            if (r.ok) {
                              const data = await r.json()
                              setJsonOut(JSON.stringify(data, null, 2))
                            }
                          } catch {}
                        }}
                        className="text-muted-foreground hover:text-foreground"
                        draggable={false}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                          <path fillRule="evenodd" d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0 0 16.5 9h-1.875a1.875 1.875 0 0 1-1.875-1.875V5.25A3.75 3.75 0 0 0 9 1.5H5.625ZM7.5 15a.75.75 0 0 1 .75-.75h7.5a.75.75 0 0 1 0 1.5h-7.5A.75.75 0 0 1 7.5 15Zm.75 2.25a.75.75 0 0 0 0 1.5H12a.75.75 0 0 0 0-1.5H8.25Z" clipRule="evenodd" />
                          <path d="M12.971 1.816A5.23 5.23 0 0 1 14.25 5.25v1.875c0 .207.168.375.375.375H16.5a5.23 5.23 0 0 1 3.434 1.279 9.768 9.768 0 0 0-6.963-6.963Z" />
                        </svg>
                      </button>
                    )}
                    <button
                      aria-label="Delete clip"
                      title="Delete clip"
                      onClick={async (e) => {
                        e.stopPropagation()
                        if (!c.ts) return
                        try {
                          const r = await fetch(`${API_BASE}/api/clips/${c.ts}`, { method: 'DELETE', credentials: 'include' })
                          if (r.ok) {
                            const list = await fetch(`${API_BASE}/api/clips`).then(r => r.json())
                            setClips(list)
                          }
                        } catch {}
                      }}
                      className="text-muted-foreground hover:text-destructive"
                      draggable={false}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                        <path fillRule="evenodd" d="M9 3.75A1.75 1.75 0 0 1 10.75 2h2.5A1.75 1.75 0 0 1 15 3.75V5h3.25a.75.75 0 0 1 0 1.5H5.75a.75.75 0 0 1 0-1.5H9V3.75ZM6.75 8.5a.75.75 0 0 1 .75.75V19c0 .69.56 1.25 1.25 1.25h6.5c.69 0 1.25-.56 1.25-1.25V9.25a.75.75 0 0 1 1.5 0V19A2.75 2.75 0 0 1 15.25 21.75h-6.5A2.75 2.75 0 0 1 6 19V9.25a.75.75 0 0 1 .75-.75Zm3 .75a.75.75 0 0 1 .75.75v7.5a.75.75 0 0 1-1.5 0v-7.5a.75.75 0 0 1 .75-.75Zm3 .75a.75.75 0 0 1 .75-.75.75.75 0 0 1 .75.75v7.5a.75.75 0 0 1-1.5 0v-7.5Z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
              {clips.length === 0 && (
                <div className="text-xs text-muted-foreground">No saved clips yet.</div>
              )}
            </div>
          </div>
        </aside>
      </main>
      {/* Removed full-screen blur overlay; using inline progress at top */}
    </div>
  )
}


