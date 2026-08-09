import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  fetchOrchestra,
  generatePiece,
  midiDownloadUrl,
  musicXmlDownloadUrl,
} from '../api'
import { ensureAudioReady, playNotes, stopPlayback } from '../audio/pianoPlayer'
import { useLocalized } from '../hooks/useLocalized'
import type { GeneratedPiece, OrchestraDetail } from '../types'

export function GeneratorPage() {
  const { id = '' } = useParams()
  const [searchParams] = useSearchParams()
  const { t } = useTranslation()
  const text = useLocalized()

  const [orchestra, setOrchestra] = useState<OrchestraDetail | null>(null)
  const [piece, setPiece] = useState<GeneratedPiece | null>(null)
  const [loadingOrch, setLoadingOrch] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoadingOrch(true)
    fetchOrchestra(id)
      .then((data) => {
        if (!cancelled) setOrchestra(data)
      })
      .catch(() => {
        if (!cancelled) setError(t('generator.loadError'))
      })
      .finally(() => {
        if (!cancelled) setLoadingOrch(false)
      })
    return () => {
      cancelled = true
      stopPlayback()
    }
  }, [id, t])

  const runGenerate = useCallback(async () => {
    setGenerating(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    try {
      const seedParam = searchParams.get('seed')
      const seed = seedParam ? Number(seedParam) : undefined
      const result = await generatePiece(id, Number.isFinite(seed) ? seed : undefined)
      setPiece(result)
    } catch {
      setError(t('generator.generateError'))
    } finally {
      setGenerating(false)
    }
  }, [id, searchParams, t])

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

  if (loadingOrch) {
    return (
      <div className="page">
        <p className="status">{t('detail.loading')}</p>
      </div>
    )
  }

  if (!orchestra) {
    return (
      <div className="page">
        <Link className="back-link" to="/orchestras">
          ← {t('detail.back')}
        </Link>
        <p className="status">{t('detail.error')}</p>
      </div>
    )
  }

  return (
    <div className="page generator">
      <Link className="back-link" to={`/orchestras/${id}`}>
        ← {text(orchestra.name)}
      </Link>
      <header className="detail-header">
        <div className="eyebrow">
          {orchestra.personality_emoji} {t('generator.title')}
        </div>
        <h1>{text(orchestra.name)}</h1>
        <p className="prose">{t('generator.lead')}</p>
      </header>

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
        <section className="generator-meta">
          <dl>
            <div>
              <dt>{t('generator.meta.rhythm')}</dt>
              <dd>{piece.rhythm_pattern}</dd>
            </div>
            <div>
              <dt>{t('generator.meta.bpm')}</dt>
              <dd>{Math.round(piece.bpm)}</dd>
            </div>
            <div>
              <dt>{t('generator.meta.key')}</dt>
              <dd>
                {piece.key}
                <span className="meta-note"> {t('generator.keyNote')}</span>
              </dd>
            </div>
            <div>
              <dt>{t('generator.meta.duration')}</dt>
              <dd>
                {Math.round(piece.duration_seconds)}
                {t('generator.seconds')}
              </dd>
            </div>
            <div>
              <dt>{t('generator.meta.seed')}</dt>
              <dd>{piece.seed}</dd>
            </div>
            <div>
              <dt>{t('generator.meta.form')}</dt>
              <dd>{piece.form.join(' → ')}</dd>
            </div>
          </dl>

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
        </section>
      )}
    </div>
  )
}
