import type {
  AtelierOptions,
  GeneratedPiece,
  LabLayer,
  LabOptions,
  LabSkeletonRequest,
  OrchestraCard,
  OrchestraDetail,
  RenderInstruments,
  Skeleton,
  SkeletonRequest,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<T>
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function fetchOrchestras() {
  return getJson<OrchestraCard[]>('/api/orchestras')
}

export function fetchOrchestra(id: string) {
  return getJson<OrchestraDetail>(`/api/orchestras/${id}`)
}

export function fetchAtelierOptions() {
  return getJson<AtelierOptions>('/api/atelier/options')
}

export function fetchLabOptions() {
  return getJson<LabOptions>('/api/lab/options')
}

export function buildLabSkeleton(body: LabSkeletonRequest) {
  return postJson<Skeleton>('/api/lab/skeleton', body)
}

export function extendLabSkeleton(body: LabSkeletonRequest & { seed: number }) {
  return postJson<Skeleton>('/api/lab/extend', body)
}

export function renderLabLayer(
  skeleton: Skeleton,
  layer: LabLayer,
  opts?: {
    ensemble_id?: string
    style_id?: string
    seed?: number
    instruments?: RenderInstruments
    generation_options?: Skeleton['generation_options']
  },
) {
  return postJson<GeneratedPiece>('/api/lab/render', {
    skeleton,
    layer,
    ensemble_id: opts?.ensemble_id,
    style_id: opts?.style_id,
    seed: opts?.seed ?? skeleton.seed,
    instruments: opts?.instruments,
    generation_options: opts?.generation_options,
  })
}

export function createSkeleton(body: SkeletonRequest) {
  return postJson<Skeleton>('/api/skeleton', body)
}

export function renderSkeleton(
  skeleton: Skeleton,
  orchestraId: string,
  opts?: { seed?: number; instruments?: RenderInstruments },
) {
  return postJson<GeneratedPiece>('/api/render', {
    skeleton,
    orchestra_id: orchestraId,
    seed: opts?.seed,
    instruments: opts?.instruments,
  })
}

export function midiDownloadUrl(orchestraId: string, seed: number) {
  return `${API_BASE}/api/generate/${orchestraId}/midi?seed=${seed}`
}

export function musicXmlDownloadUrl(orchestraId: string, seed: number) {
  return `${API_BASE}/api/generate/${orchestraId}/musicxml?seed=${seed}`
}
