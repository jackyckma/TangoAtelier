import * as Tone from 'tone'
import type { NoteEvent } from '../types'

/** Salamander grand samples (Tone.js CDN) — expressive acoustic piano. */
const SALAMANDER_BASE = 'https://tonejs.github.io/audio/salamander/'

let sampler: Tone.Sampler | null = null
let loadPromise: Promise<Tone.Sampler> | null = null

async function getSampler(): Promise<Tone.Sampler> {
  if (sampler && sampler.loaded) return sampler
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
      await Tone.loaded()
      sampler = s
      return s
    })()
  }
  return loadPromise
}

export async function ensureAudioReady() {
  await Tone.start()
  await getSampler()
}

export function stopPlayback() {
  const transport = Tone.getTransport()
  transport.stop()
  transport.cancel(0)
  sampler?.releaseAll()
}

export async function playNotes(notes: NoteEvent[], onEnded?: () => void) {
  await ensureAudioReady()
  stopPlayback()
  const s = await getSampler()
  const transport = Tone.getTransport()

  let lastEnd = 0
  for (const n of notes) {
    const dur = Math.max(0.05, n.duration)
    lastEnd = Math.max(lastEnd, n.start + n.duration)
    const vel = Math.min(1, Math.max(0.15, n.velocity / 127))
    const midiNote = Tone.Frequency(n.pitch, 'midi').toNote()
    transport.schedule((t) => {
      s.triggerAttackRelease(midiNote, dur, t, vel)
    }, n.start)
  }

  transport.schedule(() => {
    onEnded?.()
  }, lastEnd + 0.35)

  transport.start('+0.05')
}
