import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  generatePiece,
  midiDownloadUrl,
  musicXmlDownloadUrl,
} from '../api'
import { ensureAudioReady, playNotes, stopPlayback } from '../audio/pianoPlayer'
import type { GeneratedPiece } from '../types'
import { GenerationResult } from './StyleParams'

type Props = {
  orchestraId: string
}

export function InlineGenerator({ orchestraId }: Props) {
  const { t } = useTranslation()
  const [piece, setPiece] = useState<GeneratedPiece | null>(null)
  const [generating, setGenerating] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setPiece(null)
    setError(null)
    stopPlayback()
    setPlaying(false)
    return () => stopPlayback()
  }, [orchestraId])

  const runGenerate = useCallback(async () => {
    setGenerating(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    try {
      const result = await generatePiece(orchestraId)
      setPiece(result)
    } catch {
      setError(t('generator.generateError'))
    } finally {
      setGenerating(false)
    }
  }, [orchestraId, t])

  const onPlay = async () => {
    if (!piece) return
    try {
      setLoadingSamples(true)
      await ensureAudioReady()
      setLoadingSamples(false)
      setPlaying(true)
      await playNotes(piece.notes, () => setPlaying(false))
    } catch {
      setLoadingSamples(false)
      setPlaying(false)
      setError(t('generator.audioError'))
    }
  }

  const onStop = () => {
    stopPlayback()
    setPlaying(false)
  }

  return (
    <section className="inline-generator" id="listen" aria-labelledby="listen-title">
      <h2 className="section-label" id="listen-title">
        {t('generator.title')}
      </h2>
      <p className="prose params-lead">{t('generator.lead')}</p>

      <div className="generator-actions">
        <button
          type="button"
          className="btn"
          disabled={generating}
          onClick={() => void runGenerate()}
        >
          {generating ? t('generator.generating') : t('generator.generate')}
        </button>
        {piece && !playing && (
          <button
            type="button"
            className="btn btn-secondary"
            disabled={loadingSamples}
            onClick={() => void onPlay()}
          >
            {loadingSamples ? t('generator.loadingSamples') : t('generator.play')}
          </button>
        )}
        {playing && (
          <button type="button" className="btn btn-secondary" onClick={onStop}>
            {t('generator.stop')}
          </button>
        )}
      </div>

      {error && <p className="status status-error">{error}</p>}

      {piece && (
        <div className="generator-meta">
          <h3 className="params-subtitle">{t('params.thisRunTitle')}</h3>
          <GenerationResult piece={piece} />
          <div className="generator-downloads">
            <a
              className="btn btn-ghost-ink"
              href={midiDownloadUrl(piece.orchestra_id, piece.seed)}
              download
            >
              {t('generator.downloadMidi')}
            </a>
            <a
              className="btn btn-ghost-ink"
              href={musicXmlDownloadUrl(piece.orchestra_id, piece.seed)}
              download
            >
              {t('generator.downloadMusicXml')}
            </a>
          </div>
        </div>
      )}
    </section>
  )
}
