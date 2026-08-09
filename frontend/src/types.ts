export type Localized = { zh: string; en: string }

export type PersonalityType =
  | 'rhythmic'
  | 'lyrical'
  | 'smooth_powerful'
  | 'dramatic'

export type Level = 'low' | 'medium' | 'high' | 'very_high'

export type HarmonicTendencies = {
  primary_mode: string
  typical_progressions: string[]
  borrowed_chords_frequency: Level | string
  dissonance_level: Level | string
  voicing_style: string
}

export type Articulation = {
  staccato_level: Level | string
  rubato_level: Level | string
  dynamic_contrast: Level | string
  pause_frequency: Level | string
}

export type OrchestraCard = {
  id: string
  name: Localized
  personality_type: PersonalityType
  personality_emoji: string
  era: { start: number; end: number }
  sound_description: Localized
}

export type OrchestraDetail = OrchestraCard & {
  bio: Localized
  tempo_bpm_range: [number, number]
  rhythm_patterns: string[]
  harmonic_tendencies: HarmonicTendencies
  articulation: Articulation
  instrumentation_defaults: string[]
  reference_songs: { title: string; type: string }[]
}

export type NoteEvent = {
  pitch: number
  start: number
  duration: number
  velocity: number
  track: string
}

export type GeneratedPiece = {
  orchestra_id: string
  seed: number
  bpm: number
  key: string
  mode: string
  time_signature: [number, number]
  rhythm_pattern: string
  form: string[]
  bars: number
  duration_seconds: number
  chords: { bar: number; symbol: string; start: number; duration: number }[]
  notes: NoteEvent[]
  midi_base64?: string
}
