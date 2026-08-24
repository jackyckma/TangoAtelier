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

export type MelodyLevel = 'low' | 'medium' | 'high'

export type RenderInstruments = {
  piano?: boolean
  guitar?: boolean
  bandoneon?: boolean
  strings?: boolean
}

export type GenerationOptions = {
  expectancy_gate?: boolean
  surface_reharm?: 'off' | 'low' | 'on'
  motivic_cells?: 'single' | 'multi'
  phrase_transform_aggressive?: boolean
  b_groove_contrast_run?: boolean
  yeites_intensity?: 'low' | 'medium' | 'high'
  a_prime_elaboration?: boolean
  harmonic_grammar?: string
}

export type LabLayer = 'theme' | 'groove' | 'ensemble'

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
  melody_density?: MelodyLevel
  melody_variation?: MelodyLevel
  decoration?: number
  volumes?: Record<string, number>
  instruments?: RenderInstruments
  bars: number
  duration_seconds: number
  chords: {
    bar: number
    symbol: string
    start: number
    duration: number
    key?: string
    mode?: string
    section?: string
  }[]
  harmony_plan?: {
    section: string
    key: string
    mode: string
    progression_id: string
    /** Chords actually used in this section (matches the bar grid). */
    progression: string[]
    /** Full palette assigned to the section; may be longer than what fits. */
    progression_template?: string[]
    modulation?: string | null
    bar_from?: number
    bar_to?: number
  }[]
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
  harmony_plan?: {
    section: string
    key: string
    mode: string
    progression_id: string
    progression: string[]
    progression_template?: string[]
    modulation?: string | null
    bar_from?: number
    bar_to?: number
  }[]
  melody_density: MelodyLevel
  melody_variation: MelodyLevel
  drama?: {
    climax_bars: number[]
    pause_bars: number[]
    dense_bars: number[]
  }
  bars: number
  chords: {
    bar: number
    symbol: string
    start_beat: number
    duration_beats: number
    key?: string
    mode?: string
    section?: string
  }[]
  melody: {
    pitch: number
    start_beat: number
    duration_beats: number
    phrase_role?: string
    phrase_end?: boolean
  }[]
  generation_options?: GenerationOptions
  archetype_id?: string
  progression_character?: string
  segment_bars?: number
  intent_translation?: {
    tag_id: string
    label_en: string
    label_zh: string
    applied?: Record<string, unknown>
  }[]
  suggested_style_id?: string
  suggested_ensemble_id?: string
}

export type LabSkeletonRequest = {
  dance_type?: DanceType
  mode?: string
  progression_character?: string
  archetype_id?: string
  melody_density?: MelodyLevel
  melody_variation?: MelodyLevel
  intent_tags?: string[]
  generation_options?: GenerationOptions
  seed?: number
}

export type LabOptions = {
  dance_types: { id: DanceType }[]
  modes: { id: string; label: Localized }[]
  progression_characters: { id: string; label: Localized }[]
  archetypes: {
    id: string
    form_id: string
    bars: number
    label: Localized
  }[]
  intent_tags: {
    id: string
    label_en: string
    label_zh: string
    category: string
  }[]
  ensemble_presets: {
    id: string
    label: Localized
    instruments: RenderInstruments
    default_style_id?: string
  }[]
  generation_options_defaults: GenerationOptions
  style_references: {
    id: string
    personality_type: string
    personality_emoji?: string
    name?: Localized
  }[]
  segment_bars_default: number
}

export type SkeletonRequest = {
  dance_type: DanceType
  key?: string | null
  progression_id?: string | null
  form_id?: string | null
  melody_density?: MelodyLevel
  melody_variation?: MelodyLevel
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
