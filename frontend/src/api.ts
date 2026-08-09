import type {
  AtelierOptions,
  GeneratedPiece,
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
