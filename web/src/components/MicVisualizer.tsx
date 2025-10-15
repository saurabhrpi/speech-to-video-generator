import { useEffect, useRef } from 'react'

declare global {
  interface Window { webkitAudioContext?: typeof AudioContext }
}

function createAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  const Ctor = window.AudioContext || window.webkitAudioContext
  if (!Ctor) return null
  try {
    return new Ctor()
  } catch {
    return null
  }
}

type Props = { stream: MediaStream | null }

export default function MicVisualizer({ stream }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const rafRef = useRef<number | null>(null)
  const audioRef = useRef<{ ctx: AudioContext; analyser: AnalyserNode; source: MediaStreamAudioSourceNode } | null>(null)

  useEffect(() => {
    const canvasMaybe = canvasRef.current
    if (!canvasMaybe) return
    const c = canvasMaybe as HTMLCanvasElement
    const g = c.getContext('2d') as CanvasRenderingContext2D | null
    if (!g) return

    let mounted = true

    function cleanup() {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = null
      if (audioRef.current) {
        try { audioRef.current.source.disconnect() } catch {}
        try { audioRef.current.analyser.disconnect() } catch {}
        try { audioRef.current.ctx.close() } catch {}
        audioRef.current = null
      }
    }

    async function setup() {
      cleanup()
      if (!stream) return
      try {
        const ctx = createAudioContext()
        if (!ctx) return
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 2048
        const source = ctx.createMediaStreamSource(stream)
        source.connect(analyser)
        audioRef.current = { ctx, analyser, source }

        const bufferLength = analyser.frequencyBinCount
        const dataArray = new Uint8Array(bufferLength)

        function draw() {
          if (!mounted) return
          rafRef.current = requestAnimationFrame(draw)
          analyser.getByteTimeDomainData(dataArray)

          const width = c.width
          const height = c.height
          // Guard against rare null context
          const ctx = g
          if (!ctx) return
          ctx.clearRect(0, 0, width, height)
          ctx.fillStyle = 'hsl(0 0% 98%)'
          ctx.fillRect(0, 0, width, height)
          ctx.lineWidth = 2
          ctx.strokeStyle = 'hsl(221.2 83.2% 53.3%)'
          ctx.beginPath()

          const sliceWidth = width / bufferLength
          let x = 0
          for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0
            const y = (v * height) / 2
            if (i === 0) ctx.moveTo(x, y)
            else ctx.lineTo(x, y)
            x += sliceWidth
          }
          ctx.lineTo(width, height / 2)
          ctx.stroke()
        }
        draw()
      } catch (_err) {
        // noop
      }
    }

    setup()
    return () => { mounted = false; cleanup() }
  }, [stream])

  return (
    <div className="rounded-md border bg-card p-2">
      <div className="text-xs text-muted-foreground mb-1">Recording…</div>
      <canvas ref={canvasRef} width={560} height={90} className="w-full" />
    </div>
  )
}


