import type { OrchestraCard, OrchestraDetail } from './types'

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
