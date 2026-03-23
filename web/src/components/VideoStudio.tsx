import { useState, useRef } from 'react'
import { Button } from './ui/button'

const API_BASE = import.meta.env.VITE_API_BASE || ''

type VideoStudioProps = {
  busy: boolean
  onBusyChange: (b: boolean) => void
  onJsonUpdate: (json: string) => void
  onVideoUrl: (url: string | null) => void
}

export default function VideoStudio({ busy, onBusyChange, onJsonUpdate, onVideoUrl }: VideoStudioProps) {
  const [imageUrls, setImageUrls] = useState<string[]>(['', ''])
  const [model, setModel] = useState<'cheap' | 'expensive'>('cheap')
  const [videos, setVideos] = useState<string[]>([])
  const [prompts, setPrompts] = useState<string[]>([])
  const [statusMsg, setStatusMsg] = useState('')
  const [progress, setProgress] = useState(0)
  const [currentPair, setCurrentPair] = useState(0)
  const [allDone, setAllDone] = useState(false)
  const [stitching, setStitching] = useState(false)
  const [stitchedUrl, setStitchedUrl] = useState<string | null>(null)
  const resumeRef = useRef<Record<string, any> | null>(null)

  const validUrls = imageUrls.filter(u => u.trim().startsWith('http'))
  const totalTransitions = validUrls.length - 1
  const canStart = validUrls.length >= 2 && !busy

  function addImageSlot() {
    setImageUrls(prev => [...prev, ''])
  }

  function removeImageSlot(idx: number) {
    if (imageUrls.length <= 2) return
    setImageUrls(prev => prev.filter((_, i) => i !== idx))
  }

  function updateUrl(idx: number, val: string) {
    setImageUrls(prev => {
      const copy = [...prev]
      copy[idx] = val
      return copy
    })
  }

  function moveImage(fromIdx: number, toIdx: number) {
    if (toIdx < 0 || toIdx >= imageUrls.length) return
    setImageUrls(prev => {
      const copy = [...prev]
      const [item] = copy.splice(fromIdx, 1)
      copy.splice(toIdx, 0, item)
      return copy
    })
  }

  async function pollJob(jobId: string): Promise<Record<string, any> | null> {
    const maxFails = 5
    let failCount = 0
    while (true) {
      await new Promise(r => setTimeout(r, 3000))
      try {
        const resp = await fetch(`${API_BASE}/api/jobs/${jobId}`)
        if (resp.status === 404) {
          setStatusMsg('Job lost — server may have restarted.')
          return null
        }
        const data = await resp.json()
        failCount = 0

        const msg = (data.message as string) || 'Processing...'
        setStatusMsg(msg)

        if (data.partial_result) {
                  resumeRef.current = data.partial_result
                  const vids = data.partial_result.transition_videos || []
                  const prms = data.partial_result.transition_prompts || []
                  setVideos(vids)
                  setPrompts(prms)
                  onJsonUpdate(JSON.stringify(data.partial_result, null, 2))
                }

        const doneVideos = resumeRef.current?.transition_videos?.length || 0
        const pct = totalTransitions > 0 ? Math.round((doneVideos / totalTransitions) * 100) : 0
        setProgress(pct)

        if (data.status === 'completed' || data.status === 'failed') {
          return data.result as Record<string, any> | null
        }
      } catch {
        failCount++
        if (failCount >= maxFails) {
          setStatusMsg('Lost connection to server.')
          return null
        }
      }
    }
  }

  async function runGeneration(stopAfter: string | null, resumeState: Record<string, any> | null) {
    onBusyChange(true)
    setStatusMsg('Starting video generation...')
    setAllDone(false)

    try {
      const resp = await fetch(`${API_BASE}/api/generate/custom-videos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          image_urls: validUrls,
          model,
          stop_after: stopAfter,
          resume_state: resumeState,
        }),
      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Server error' }))
        setStatusMsg(`Error: ${err.detail || 'Request failed'}`)
        return
      }

      const { job_id } = await resp.json()
      if (!job_id) {
        setStatusMsg('No job ID returned.')
        return
      }

      const result = await pollJob(job_id)
      if (!result) return

      if (!result.success) {
        setStatusMsg(`Error: ${typeof result.error === 'string' ? result.error : 'Generation failed'}`)
        resumeRef.current = result
        return
      }

      setVideos(result.transition_videos || [])
      setPrompts(result.transition_prompts || [])
      resumeRef.current = result
      onJsonUpdate(JSON.stringify(result, null, 2))

      if (result.phase_completed === 'all_done') {
        setAllDone(true)
        setProgress(100)
        setStatusMsg('All transitions complete!')
      } else {
        const completedCount = (result.transition_videos || []).length
        setCurrentPair(completedCount)
        setProgress(Math.round((completedCount / totalTransitions) * 100))
        setStatusMsg(`Transition ${completedCount} of ${totalTransitions} complete — review below.`)
      }
    } catch {
      setStatusMsg('Network error — could not reach server.')
    } finally {
      onBusyChange(false)
    }
  }

  function handleGenerateNext() {
    const nextIdx = videos.length
    const stopAfter = `video_${nextIdx + 1}`
    runGeneration(stopAfter, resumeRef.current)
  }

  function handleGenerateAll() {
    runGeneration(null, resumeRef.current)
  }

  function handleStartOver() {
    setVideos([])
    setPrompts([])
    setStatusMsg('')
    setProgress(0)
    setCurrentPair(0)
    setAllDone(false)
    setStitching(false)
    setStitchedUrl(null)
    onJsonUpdate('')
    onVideoUrl(null)
    resumeRef.current = null
  }

  async function handleStitch() {
    if (videos.length < 1) return
    setStitching(true)
    onBusyChange(true)
    setStatusMsg('Stitching final video...')

    try {
      const resp = await fetch(`${API_BASE}/api/generate/stitch-custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ video_urls: videos }),
      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Stitch failed' }))
        setStatusMsg(`Stitch error: ${err.detail || 'Request failed'}`)
        return
      }

      const data = await resp.json()
      if (data.success && data.stitched_url) {
        setStitchedUrl(data.stitched_url)
        onVideoUrl(data.stitched_url)
        setStatusMsg('Final video stitched!')
        const updatedResult = { ...(resumeRef.current || {}), stitched_url: data.stitched_url }
        onJsonUpdate(JSON.stringify(updatedResult, null, 2))
      } else {
        setStatusMsg(`Stitch error: ${data.error || 'Unknown error'}`)
      }
    } catch {
      setStatusMsg('Network error during stitching.')
    } finally {
      setStitching(false)
      onBusyChange(false)
    }
  }

  const hasStarted = videos.length > 0 || busy

  return (
    <div className="space-y-6">
      <div className="rounded-md border bg-card p-4 space-y-4">
        <h3 className="text-sm font-semibold">Images</h3>
        <p className="text-xs text-muted-foreground">
          Paste image URLs in order. Transition videos will be generated between each consecutive pair.
        </p>

        <div className="space-y-2">
          {imageUrls.map((url, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground w-12 shrink-0">Pic {idx + 1}</span>
              <input
                type="text"
                placeholder="https://cdn.example.com/image.png"
                value={url}
                onChange={e => updateUrl(idx, e.target.value)}
                className="flex-1 rounded border bg-background px-2 py-1.5 text-xs outline-none focus:ring-1 focus:ring-primary"
                disabled={busy}
              />
              {url.trim().startsWith('http') && (
                <img src={url} alt={`Pic ${idx + 1}`} className="h-10 w-10 rounded border object-cover shrink-0" />
              )}
              <div className="flex flex-col gap-0.5">
                <button
                  onClick={() => moveImage(idx, idx - 1)}
                  disabled={idx === 0 || busy}
                  className="text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                  title="Move up"
                >▲</button>
                <button
                  onClick={() => moveImage(idx, idx + 1)}
                  disabled={idx === imageUrls.length - 1 || busy}
                  className="text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                  title="Move down"
                >▼</button>
              </div>
              <button
                onClick={() => removeImageSlot(idx)}
                disabled={imageUrls.length <= 2 || busy}
                className="text-xs text-muted-foreground hover:text-destructive disabled:opacity-30"
                title="Remove"
              >✕</button>
            </div>
          ))}
        </div>

        <Button variant="outline" size="sm" onClick={addImageSlot} disabled={busy}>
          + Add Image
        </Button>

        <div className="flex items-center gap-3 pt-2">
          <label className="text-xs font-medium">Model:</label>
          <select
            value={model}
            onChange={e => setModel(e.target.value as 'cheap' | 'expensive')}
            className="rounded border bg-background px-2 py-1 text-xs outline-none"
            disabled={busy}
          >
            <option value="cheap">Cheap (Hailuo)</option>
            <option value="expensive">Expensive (Kling Pro)</option>
          </select>
        </div>

        <div className="flex gap-2 pt-2">
          {!hasStarted ? (
            <Button onClick={handleGenerateNext} disabled={!canStart}>
              Generate Next Video
            </Button>
          ) : (
            <>
              {!allDone && videos.length < totalTransitions && (
                <>
                  <Button onClick={handleGenerateNext} disabled={busy}>
                    Generate Next Video
                  </Button>
                  <Button variant="secondary" onClick={handleGenerateAll} disabled={busy}>
                    Generate Remaining
                  </Button>
                </>
              )}
              <Button variant="outline" onClick={handleStartOver} disabled={busy}>
                Start Over
              </Button>
            </>
          )}
        </div>
      </div>

      {(busy || statusMsg) && (
        <div className="rounded-md border bg-card p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">{statusMsg || 'Processing…'}</span>
            <span className="text-xs text-muted-foreground">{Math.round(progress)}%</span>
          </div>
          <div className="mt-2 h-2 w-full rounded bg-muted">
            <div
              className="h-2 rounded bg-primary"
              style={{ width: `${Math.max(0, Math.min(progress, 100))}%`, transition: 'width 160ms linear' }}
            />
          </div>
        </div>
      )}

      {videos.length > 0 && (
        <div className="rounded-md border bg-card p-4 space-y-4">
          <h3 className="text-sm font-semibold">
            Transition Videos ({videos.length} of {totalTransitions})
          </h3>
          <div className="space-y-4">
            {videos.map((url, i) => (
              <div key={i} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-muted-foreground">
                    Transition {i + 1}: Pic {i + 1} → Pic {i + 2}
                  </span>
                </div>
                {prompts[i] && (
                  <p className="text-xs text-muted-foreground bg-muted rounded px-2 py-1">
                    Prompt: {prompts[i]}
                  </p>
                )}
                <video
                  src={url}
                  controls
                  className="w-full max-w-2xl rounded border"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {allDone && videos.length > 0 && (
        <div className="rounded-md border border-green-500/30 bg-green-500/5 p-4 space-y-3">
          <p className="text-sm text-green-700 dark:text-green-400 font-medium">
            All {videos.length} transition videos generated successfully.
          </p>
          {!stitchedUrl && (
            <Button onClick={handleStitch} disabled={stitching || busy}>
              {stitching ? 'Stitching…' : 'Stitch Final Video'}
            </Button>
          )}
        </div>
      )}

      {stitchedUrl && (
        <div className="rounded-md border bg-card p-4 space-y-3">
          <h3 className="text-sm font-semibold">Final Stitched Video</h3>
          <video
            src={`${API_BASE}${stitchedUrl}`}
            controls
            className="w-full max-w-2xl rounded border"
          />
        </div>
      )}
    </div>
  )
}
