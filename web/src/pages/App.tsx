import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../components/ui/button'
import MicVisualizer from '../components/MicVisualizer'

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
  const fileRef = useRef<HTMLInputElement | null>(null)
  const [loginRequired, setLoginRequired] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [pendingAudio, setPendingAudio] = useState<File | null>(null)
  const [pendingTranscript, setPendingTranscript] = useState<string>('')

  const canRecord = useMemo(() => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia), [])
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recording, setRecording] = useState(false)
  const recordedChunks = useRef<Blob[]>([])
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/clips`).then(r => r.json()).then((list) => { setClips(list); clipCountRef.current = Array.isArray(list) ? list.length : 0 }).catch(() => setClips([]))
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

  // Removed prompt generation

  async function handleSpeechToVideo(file: File) {
    setBusy(true)
    try {
      // 2 minutes target for generation via audio
      beginProgress('Processing audio…', 120_000)
      const body = new FormData()
      body.set('audio', file)
      const resp = await fetch(`${API_BASE}/api/speech-to-video`, { method: 'POST', body })
      if (resp.status === 401) {
        setLoginRequired(true)
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Sign in required to continue.')
        setBusy(false)
        return
      }
      const data: ApiResult = await resp.json()
      setJsonOut(JSON.stringify(data, null, 2))
      const url = data.video_url as string | undefined
      if (url) {
        setStatusMsg('Preparing video…')
        setPendingUrl(url)
        await preloadVideo(url)
        const elapsed = performance.now() - startTsRef.current
        const finish = () => {
          setVideoUrl(url)
          setPendingUrl(null)
          endProgress('Ready')
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
    const ok = window.confirm('Stitch all saved clips now? This may take some time.')
    if (!ok) return
    setBusy(true)
    try {
      // 45 seconds per 2 clips (ceil)
      const clipsCount = clipCountRef.current > 0 ? clipCountRef.current : clips.length
      const stitchExpected = 45_000 * Math.max(1, Math.ceil(clipsCount / 2))
      beginProgress('Stitching saved clips…', stitchExpected)
      const body = new FormData()
      body.set('use_saved', 'true')
      const resp = await fetch(`${API_BASE}/api/stitch`, { method: 'POST', body })
      if (resp.status === 401) {
        setLoginRequired(true)
        clearProgressTimer()
        setProgress(0)
        setStatusMsg('Sign in required to continue.')
        setBusy(false)
        return
      }
      const data: ApiResult = await resp.json()
      setJsonOut(JSON.stringify(data, null, 2))
      if (data.success) {
        const url = `${API_BASE}/api/stitched`
        setStatusMsg('Preparing video…')
        setPendingUrl(url)
        await preloadVideo(url)
        const elapsed = performance.now() - startTsRef.current
        const finish = () => {
          setVideoUrl(url)
          setPendingUrl(null)
          endProgress('Stitching complete')
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

  function signIn() {
    window.location.href = `${API_BASE}/api/auth/login`
  }

  async function confirmProceed() {
    const f = pendingAudio
    setConfirmOpen(false)
    if (f) {
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

  return (
    <div className="min-h-dvh bg-background">
      <header className="border-b">
        <div className="container py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Speech to Video</h1>
          <div>
            <Button variant="outline" onClick={signIn}>Sign in</Button>
          </div>
        </div>
      </header>

      <main className="container py-8 space-y-8">
        {confirmOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="w-full max-w-md rounded-md border bg-card p-5 shadow">
              <h2 className="text-base font-semibold">Submit recording?</h2>
              <p className="mt-2 text-sm text-muted-foreground">{pendingTranscript ? 'Proceed to generate a video from your recorded audio?' : 'Just a sec..'}</p>
              {pendingTranscript && (
                <div className="mt-3 rounded bg-muted p-2 text-xs whitespace-pre-wrap max-h-40 overflow-auto">
                  {pendingTranscript}
                </div>
              )}
              <div className="mt-4 flex justify-end gap-2">
                <Button variant="ghost" onClick={confirmCancel}>Cancel</Button>
                <Button onClick={confirmProceed}>Proceed</Button>
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
        <section className="space-y-3">
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
            <Button variant="secondary" disabled={!videoUrl} onClick={() => handleSaveLastClip('')}>Save last clip</Button>
            <Button variant="outline" onClick={handleStitchSaved} disabled={busy}>Stitch saved clips</Button>
            <Button variant="ghost" onClick={handleClearClips}>Clear clips</Button>
          </div>
          <div className="max-w-3xl mx-auto space-y-2">
            <label className="text-sm font-medium">Saved clips</label>
            <ul className="space-y-1 text-sm">
              {clips.map((c, idx) => (
                <li key={idx} className="truncate">{c.url}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="max-w-3xl mx-auto space-y-2">
          <label className="text-sm font-medium">Result JSON</label>
          <pre className="min-h-40 max-h-80 overflow-auto rounded-md border bg-muted p-3 text-xs">
            {jsonOut || '{\n  "result": null\n}'}
          </pre>
        </section>
      </main>
      {/* Removed full-screen blur overlay; using inline progress at top */}
    </div>
  )
}


