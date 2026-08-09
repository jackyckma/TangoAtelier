export type Localized = { zh: string; en: string }

export type PersonalityType =
  | 'rhythmic'
  | 'lyrical'
  | 'smooth_powerful'
  | 'dramatic'
  | 'neutral'

export type Level = 'low' | 'medium' | 'high' | 'very_high'
export type DanceType = 'tango' | 'milonga' | 'vals'

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
  skeleton_seed?: number
  seed: number
  bpm: number
  key: string
  mode: string
  dance_type?: DanceType
  time_signature: [number, number]
  rhythm_pattern: string
  form: string[]
  progression_id?: string
  bars: number
  duration_seconds: number
  chords: { bar: number; symbol: string; start: number; duration: number }[]
  notes: NoteEvent[]
  midi_base64?: string
}

export type Skeleton = {
  seed: number
  dance_type: DanceType
  key: string
  mode: string
  tonic: number
  time_signature: [number, number]
  beats_per_bar: number
  default_bpm: number
  form_id: string
  form: string[]
  progression_id: string
  progression: string[]
  bars: number
  chords: {
    bar: number
    symbol: string
    start_beat: number
    duration_beats: number
  }[]
  melody: { pitch: number; start_beat: number; duration_beats: number }[]
}

export type SkeletonRequest = {
  dance_type: DanceType
  key?: string | null
  progression_id?: string | null
  form_id?: string | null
  seed?: number
}

export type AtelierOptions = {
  dance_types: { id: DanceType }[]
  keys: string[]
  forms: { id: string }[]
  progressions: {
    minor: { id: string }[]
    major: { id: string }[]
  }
  render_styles: {
    id: string
    personality_type: string
    personality_emoji?: string
    name?: Localized
  }[]
}
