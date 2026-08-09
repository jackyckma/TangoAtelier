import type { GeneratedPiece, OrchestraCard, OrchestraDetail } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function fetchOrchestras() {
  return getJson<OrchestraCard[]>('/api/orchestras')
}

export function fetchOrchestra(id: string) {
  return getJson<OrchestraDetail>(`/api/orchestras/${id}`)
}

export async function generatePiece(orchestraId: string, seed?: number) {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ orchestra_id: orchestraId, seed }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<GeneratedPiece>
}

export function midiDownloadUrl(orchestraId: string, seed: number) {
  return `${API_BASE}/api/generate/${orchestraId}/midi?seed=${seed}`
}

export function musicXmlDownloadUrl(orchestraId: string, seed: number) {
  return `${API_BASE}/api/generate/${orchestraId}/musicxml?seed=${seed}`
}
