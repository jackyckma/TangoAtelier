import * as Tone from 'tone'
import type { NoteEvent } from '../types'

/** Salamander grand samples (Tone.js CDN) — expressive acoustic piano. */
const SALAMANDER_BASE = 'https://tonejs.github.io/audio/salamander/'

let sampler: Tone.Sampler | null = null
let bandoneon: Tone.PolySynth | null = null
let violin: Tone.PolySynth | null = null
let cello: Tone.PolySynth | null = null
let loadPromise: Promise<void> | null = null

export type PlaybackHandlers = {
  onEnded?: () => void
  /** Called when playback enters a bar (0-based). */
  onBar?: (barIndex: number) => void
  /** Bar length in seconds — required for onBar scheduling. */
  barDurationSeconds?: number
  bars?: number
}

async function ensureInstruments(): Promise<void> {
  if (sampler?.loaded && bandoneon && violin && cello) return
  if (!loadPromise) {
    loadPromise = (async () => {
      const s = new Tone.Sampler({
        urls: {
          A0: 'A0.mp3',
          C1: 'C1.mp3',
          'D#1': 'Ds1.mp3',
          'F#1': 'Fs1.mp3',
          A1: 'A1.mp3',
          C2: 'C2.mp3',
          'D#2': 'Ds2.mp3',
          'F#2': 'Fs2.mp3',
          A2: 'A2.mp3',
          C3: 'C3.mp3',
          'D#3': 'Ds3.mp3',
          'F#3': 'Fs3.mp3',
          A3: 'A3.mp3',
          C4: 'C4.mp3',
          'D#4': 'Ds4.mp3',
          'F#4': 'Fs4.mp3',
          A4: 'A4.mp3',
          C5: 'C5.mp3',
          'D#5': 'Ds5.mp3',
          'F#5': 'Fs5.mp3',
          A5: 'A5.mp3',
          C6: 'C6.mp3',
          'D#6': 'Ds6.mp3',
          'F#6': 'Fs6.mp3',
          A6: 'A6.mp3',
          C7: 'C7.mp3',
          'D#7': 'Ds7.mp3',
          'F#7': 'Fs7.mp3',
          A7: 'A7.mp3',
          C8: 'C8.mp3',
        },
        release: 1.2,
        baseUrl: SALAMANDER_BASE,
      }).toDestination()

      // Interim stand-ins until real bandoneón / string samples
      const bn = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'sawtooth' },
        envelope: { attack: 0.08, decay: 0.3, sustain: 0.65, release: 0.6 },
      }).toDestination()
      bn.volume.value = -12
      bn.maxPolyphony = 8

      // Violin: brighter, quicker bow attack
      const vn = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'sawtooth' },
        envelope: { attack: 0.18, decay: 0.35, sustain: 0.7, release: 1.1 },
      }).toDestination()
      vn.volume.value = -18
      vn.maxPolyphony = 6

      // Cello: darker, slower pad under the band
      const vc = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { attack: 0.35, decay: 0.45, sustain: 0.8, release: 1.6 },
      }).toDestination()
      vc.volume.value = -15
      vc.maxPolyphony = 6

      await Tone.loaded()
      sampler = s
      bandoneon = bn
      violin = vn
      cello = vc
    })()
  }
  await loadPromise
}

export async function ensureAudioReady() {
  await Tone.start()
  await ensureInstruments()
}

export function stopPlayback() {
  const transport = Tone.getTransport()
  transport.stop()
  transport.cancel(0)
  sampler?.releaseAll()
  bandoneon?.releaseAll()
  violin?.releaseAll()
  cello?.releaseAll()
}

function trigger(
  track: string,
  midiNote: string,
  dur: number,
  time: number,
  vel: number,
) {
  if (track === 'bandoneon' && bandoneon) {
    bandoneon.triggerAttackRelease(midiNote, dur, time, vel * 0.55)
    return
  }
  if ((track === 'violin' || track === 'strings') && violin) {
    violin.triggerAttackRelease(midiNote, dur, time, vel * 0.38)
    return
  }
  if (track === 'cello' && cello) {
    cello.triggerAttackRelease(midiNote, dur, time, vel * 0.42)
    return
  }
  sampler?.triggerAttackRelease(midiNote, dur, time, vel)
}

export async function playNotes(
  notes: NoteEvent[],
  handlers?: PlaybackHandlers | (() => void),
) {
  const h: PlaybackHandlers =
    typeof handlers === 'function' ? { onEnded: handlers } : handlers ?? {}

  await ensureAudioReady()
  stopPlayback()
  const transport = Tone.getTransport()

  let lastEnd = 0
  for (const n of notes) {
    const dur = Math.max(0.05, n.duration)
    lastEnd = Math.max(lastEnd, n.start + n.duration)
    const vel = Math.min(1, Math.max(0.12, n.velocity / 127))
    const midiNote = Tone.Frequency(n.pitch, 'midi').toNote()
    const track = n.track || 'piano_rh'
    transport.schedule((t) => {
      trigger(track, midiNote, dur, t, vel)
    }, n.start)
  }

  const barDur = h.barDurationSeconds
  const barCount = h.bars ?? 0
  if (h.onBar && barDur && barDur > 0 && barCount > 0) {
    for (let b = 0; b < barCount; b++) {
      const bar = b
      transport.schedule((time) => {
        Tone.getDraw().schedule(() => {
          h.onBar?.(bar)
        }, time)
      }, bar * barDur)
    }
  }

  transport.schedule((time) => {
    Tone.getDraw().schedule(() => {
      h.onEnded?.()
    }, time)
  }, lastEnd + 0.35)

  transport.start('+0.05')
}
