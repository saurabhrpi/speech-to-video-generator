import { useEffect, useState } from 'react'
import { Button } from './ui/button'

const API_BASE = import.meta.env.VITE_API_BASE || ''

interface TimelapseOptions {
  room_types: { value: string; label: string }[]
  styles: { value: string; label: string }[]
  lighting_options: { value: string; label: string }[]
  camera_options: { value: string; label: string }[]
  progression_types: { value: string; label: string }[]
  suggested_features: string[]
  suggested_materials: string[]
}

interface TimelapseFormProps {
  busy: boolean
  onSubmit: (payload: Record<string, any>) => void
  stepByStep?: boolean
  onStepByStepChange?: (v: boolean) => void
  onVideoModelChange?: (v: string) => void
}

export default function TimelapseForm({ busy, onSubmit, stepByStep, onStepByStepChange, onVideoModelChange }: TimelapseFormProps) {
  const [options, setOptions] = useState<TimelapseOptions | null>(null)
  const [roomType, setRoomType] = useState('')
  const [style, setStyle] = useState('')
  const [features, setFeatures] = useState<string[]>([])
  const [featureInput, setFeatureInput] = useState('')
  const [materials, setMaterials] = useState<string[]>([])
  const [materialInput, setMaterialInput] = useState('')
  const [lighting, setLighting] = useState('natural')
  const [cameraMotion, setCameraMotion] = useState('slow_pan')
  const [progression, setProgression] = useState('construction')
  const [videoModel, setVideoModel] = useState<'cheap' | 'expensive'>('cheap')
  const [freeform, setFreeform] = useState('')

  const [showFeatureSuggestions, setShowFeatureSuggestions] = useState(false)
  const [showMaterialSuggestions, setShowMaterialSuggestions] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/api/timelapse/options`)
      .then(r => r.json())
      .then(setOptions)
      .catch(() => {})
  }, [])

  function addFeature(f: string) {
    const trimmed = f.trim().toLowerCase()
    if (trimmed && !features.includes(trimmed)) {
      setFeatures(prev => [...prev, trimmed])
    }
    setFeatureInput('')
    setShowFeatureSuggestions(false)
  }

  function removeFeature(f: string) {
    setFeatures(prev => prev.filter(x => x !== f))
  }

  function addMaterial(m: string) {
    const trimmed = m.trim().toLowerCase()
    if (trimmed && !materials.includes(trimmed)) {
      setMaterials(prev => [...prev, trimmed])
    }
    setMaterialInput('')
    setShowMaterialSuggestions(false)
  }

  function removeMaterial(m: string) {
    setMaterials(prev => prev.filter(x => x !== m))
  }

  function handleSubmit() {
    if (!roomType || !style) return
    onSubmit({
      room_type: roomType,
      style,
      features,
      materials,
      lighting,
      camera_motion: cameraMotion,
      progression,
      video_model: videoModel,
      freeform_description: freeform,
    })
  }

  const filteredFeatureSuggestions = (options?.suggested_features || []).filter(
    f => !features.includes(f) && f.includes(featureInput.toLowerCase())
  )

  const filteredMaterialSuggestions = (options?.suggested_materials || []).filter(
    m => !materials.includes(m) && m.includes(materialInput.toLowerCase())
  )

  if (!options) {
    return <div className="text-sm text-muted-foreground">Loading options...</div>
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Room Type */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Room Type *</label>
          <select
            value={roomType}
            onChange={e => setRoomType(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Select room...</option>
            {options.room_types.map(r => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        {/* Style */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Style *</label>
          <select
            value={style}
            onChange={e => setStyle(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Select style...</option>
            {options.styles.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Lighting */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Lighting</label>
          <select
            value={lighting}
            onChange={e => setLighting(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            {options.lighting_options.map(l => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </div>

        {/* Camera Motion */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Camera Motion</label>
          <select
            value={cameraMotion}
            onChange={e => setCameraMotion(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            {options.camera_options.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        {/* Progression */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Build Progression</label>
          <select
            value={progression}
            onChange={e => setProgression(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            {options.progression_types.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        {/* Video Model */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Video Model</label>
          <select
            value={videoModel}
            onChange={e => { const v = e.target.value as 'cheap' | 'expensive'; setVideoModel(v); onVideoModelChange?.(v) }}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="cheap">Cheap (Hailuo)</option>
            <option value="expensive">Expensive (Kling Pro)</option>
          </select>
        </div>
      </div>

      {/* Features */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Features</label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {features.map(f => (
            <span key={f} className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
              {f}
              <button onClick={() => removeFeature(f)} className="hover:text-destructive">&times;</button>
            </span>
          ))}
        </div>
        <div className="relative">
          <input
            type="text"
            value={featureInput}
            onChange={e => { setFeatureInput(e.target.value); setShowFeatureSuggestions(true) }}
            onFocus={() => setShowFeatureSuggestions(true)}
            onBlur={() => setTimeout(() => setShowFeatureSuggestions(false), 200)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addFeature(featureInput) } }}
            placeholder="Type a feature and press Enter..."
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          {showFeatureSuggestions && featureInput.length > 0 && filteredFeatureSuggestions.length > 0 && (
            <div className="absolute z-10 mt-1 w-full max-h-40 overflow-y-auto rounded-md border bg-popover shadow-md">
              {filteredFeatureSuggestions.map(f => (
                <button
                  key={f}
                  onMouseDown={e => { e.preventDefault(); addFeature(f) }}
                  className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                >
                  {f}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Materials */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Materials <span className="text-muted-foreground font-normal">(optional)</span></label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {materials.map(m => (
            <span key={m} className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
              {m}
              <button onClick={() => removeMaterial(m)} className="hover:text-destructive">&times;</button>
            </span>
          ))}
        </div>
        <div className="relative">
          <input
            type="text"
            value={materialInput}
            onChange={e => { setMaterialInput(e.target.value); setShowMaterialSuggestions(true) }}
            onFocus={() => setShowMaterialSuggestions(true)}
            onBlur={() => setTimeout(() => setShowMaterialSuggestions(false), 200)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addMaterial(materialInput) } }}
            placeholder="Type a material and press Enter..."
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          {showMaterialSuggestions && materialInput.length > 0 && filteredMaterialSuggestions.length > 0 && (
            <div className="absolute z-10 mt-1 w-full max-h-40 overflow-y-auto rounded-md border bg-popover shadow-md">
              {filteredMaterialSuggestions.map(m => (
                <button
                  key={m}
                  onMouseDown={e => { e.preventDefault(); addMaterial(m) }}
                  className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Freeform */}
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Additional Description <span className="text-muted-foreground font-normal">(optional)</span></label>
        <textarea
          value={freeform}
          onChange={e => setFreeform(e.target.value)}
          placeholder="Any extra creative direction, e.g. 'river pebbles under the glass steps with soft mist'..."
          rows={2}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring resize-none"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={!!stepByStep}
          onChange={e => onStepByStepChange?.(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 accent-primary"
        />
        <span className="text-sm font-medium">Step-by-step mode</span>
        <span className="text-xs text-muted-foreground">(review each phase before proceeding)</span>
      </label>

      <Button
        className="w-full h-12"
        onClick={handleSubmit}
        disabled={busy || !roomType || !style}
      >
        {busy ? 'Generating...' : 'Generate Timelapse'}
      </Button>
    </div>
  )
}
