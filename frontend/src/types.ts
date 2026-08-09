export type Localized = { zh: string; en: string }

export type PersonalityType =
  | 'rhythmic'
  | 'lyrical'
  | 'smooth_powerful'
  | 'dramatic'

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
  reference_songs: { title: string; type: string }[]
}
