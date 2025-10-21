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
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement | null>(null)
  const [loginRequired, setLoginRequired] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [pendingAudio, setPendingAudio] = useState<File | null>(null)
  const [pendingTranscript, setPendingTranscript] = useState<string>('')
  const [auth, setAuth] = useState<{ authenticated: boolean; user?: any; usage_count: number; limit: number } | null>(null)

  const canRecord = useMemo(() => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia), [])
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recording, setRecording] = useState(false)
  const recordedChunks = useRef<Blob[]>([])
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(null)

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
        resp = await fetch(`${API_BASE}/api/speech-to-video`, { method: 'POST', body })
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
          <div className="flex items-center gap-2">
            {auth?.authenticated && <span className="text-xs text-muted-foreground">Signed in as {auth?.user?.email || 'user'}</span>}
            <Button variant="outline" onClick={auth?.authenticated ? signOut : signIn}>{auth?.authenticated ? 'Sign out' : 'Sign in'}</Button>
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
            <Button variant="outline" disabled={!videoUrl} onClick={() => handleSaveLastClip('')}>Save last clip</Button>
            <Button variant="outline" onClick={handleStitchSaved} disabled={busy}>Stitch saved clips</Button>
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
                    className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                    draggable={false}
                  >
                    {/* Trash icon */}
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
                      <path fillRule="evenodd" d="M9 3.75A1.75 1.75 0 0 1 10.75 2h2.5A1.75 1.75 0 0 1 15 3.75V5h3.25a.75.75 0 0 1 0 1.5H5.75a.75.75 0 0 1 0-1.5H9V3.75ZM6.75 8.5a.75.75 0 0 1 .75.75V19c0 .69.56 1.25 1.25 1.25h6.5c.69 0 1.25-.56 1.25-1.25V9.25a.75.75 0 0 1 1.5 0V19A2.75 2.75 0 0 1 15.25 21.75h-6.5A2.75 2.75 0 0 1 6 19V9.25a.75.75 0 0 1 .75-.75Zm3 .75a.75.75 0 0 1 .75.75v7.5a.75.75 0 0 1-1.5 0v-7.5a.75.75 0 0 1 .75-.75Zm3 .75a.75.75 0 0 1 .75-.75.75.75 0 0 1 .75.75v7.5a.75.75 0 0 1-1.5 0v-7.5Z" clipRule="evenodd" />
                    </svg>
                  </button>
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


