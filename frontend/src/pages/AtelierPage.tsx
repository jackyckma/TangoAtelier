import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  createSkeleton,
  fetchAtelierOptions,
  renderSkeleton,
} from '../api'
import { ensureAudioReady, playNotes, stopPlayback } from '../audio/pianoPlayer'
import { useLocalized } from '../hooks/useLocalized'
import type {
  AtelierOptions,
  DanceType,
  GeneratedPiece,
  MelodyLevel,
  RenderInstruments,
  Skeleton,
} from '../types'

const LEVELS: MelodyLevel[] = ['low', 'medium', 'high']

const DEFAULT_INSTRUMENTS: RenderInstruments = {
  piano: true,
  bandoneon: false,
  strings: false,
}

export function AtelierPage() {
  const { t } = useTranslation()
  const text = useLocalized()
  const [searchParams] = useSearchParams()
  const preferredStyle = searchParams.get('style') || 'simple'

  const [options, setOptions] = useState<AtelierOptions | null>(null)
  const [danceType, setDanceType] = useState<DanceType>('tango')
  const [key, setKey] = useState('random')
  const [progressionId, setProgressionId] = useState('random')
  const [formId, setFormId] = useState('intro_aa_coda')
  const [melodyDensity, setMelodyDensity] = useState<MelodyLevel>('medium')
  const [melodyVariation, setMelodyVariation] = useState<MelodyLevel>('medium')
  const [skeleton, setSkeleton] = useState<Skeleton | null>(null)
  const [styleId, setStyleId] = useState(preferredStyle)
  const [piece, setPiece] = useState<GeneratedPiece | null>(null)
  const [instruments, setInstruments] =
    useState<RenderInstruments>(DEFAULT_INSTRUMENTS)
  const [instrumentsTouched, setInstrumentsTouched] = useState(false)
  const [busy, setBusy] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAtelierOptions()
      .then(setOptions)
      .catch(() => setError(t('atelier.optionsError')))
    return () => stopPlayback()
  }, [t])

  useEffect(() => {
    if (preferredStyle) setStyleId(preferredStyle)
  }, [preferredStyle])

  const progressionChoices = useMemo(() => {
    if (!options) return []
    const ids = new Set([
      ...options.progressions.minor.map((p) => p.id),
      ...options.progressions.major.map((p) => p.id),
    ])
    return ['random', ...ids]
  }, [options])

  const syncInstruments = (rendered: GeneratedPiece) => {
    if (rendered.instruments) {
      setInstruments({
        piano: rendered.instruments.piano ?? true,
        bandoneon: rendered.instruments.bandoneon ?? false,
        strings: rendered.instruments.strings ?? false,
      })
    }
  }

  const onBuildSkeleton = async () => {
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    setPiece(null)
    setInstrumentsTouched(false)
    try {
      const sk = await createSkeleton({
        dance_type: danceType,
        key: key === 'random' ? 'random' : key,
        progression_id: progressionId,
        form_id: formId,
        melody_density: melodyDensity,
        melody_variation: melodyVariation,
      })
      setSkeleton(sk)
      const simple = await renderSkeleton(sk, 'simple')
      setPiece(simple)
      setStyleId('simple')
      syncInstruments(simple)
    } catch {
      setError(t('atelier.skeletonError'))
    } finally {
      setBusy(false)
    }
  }

  const onRenderStyle = async (id: string) => {
    if (!skeleton) return
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    setStyleId(id)
    try {
      const rendered = await renderSkeleton(skeleton, id, {
        instruments: instrumentsTouched ? instruments : undefined,
      })
      setPiece(rendered)
      if (!instrumentsTouched) syncInstruments(rendered)
    } catch {
      setError(t('atelier.renderError'))
    } finally {
      setBusy(false)
    }
  }

  const onToggleInstrument = async (keyName: keyof RenderInstruments) => {
    if (!skeleton || !piece) return
    const next = {
      ...instruments,
      [keyName]: !instruments[keyName],
    }
    // Keep piano as the floor for learning; still allow toggle if user insists
    setInstruments(next)
    setInstrumentsTouched(true)
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    try {
      const rendered = await renderSkeleton(skeleton, styleId, {
        instruments: next,
      })
      setPiece(rendered)
    } catch {
      setError(t('atelier.renderError'))
    } finally {
      setBusy(false)
    }
  }

  const onPlay = async () => {
    if (!piece) return
    try {
      await ensureAudioReady()
      setPlaying(true)
      await playNotes(piece.notes, () => setPlaying(false))
    } catch {
      setPlaying(false)
      setError(t('generator.audioError'))
    }
  }

  const onStop = () => {
    stopPlayback()
    setPlaying(false)
  }

  const styleLabel = (id: string) => {
    if (id === 'simple') return t('atelier.simpleStyle')
    const s = options?.render_styles.find((x) => x.id === id)
    if (s?.name) return text(s.name)
    return id
  }

  const levelLabel = (level: MelodyLevel) => t(`atelier.levels.${level}`)

  return (
    <div className="page atelier-page">
      <header className="detail-header">
        <div className="eyebrow">{t('atelier.eyebrow')}</div>
        <h1>{t('atelier.title')}</h1>
        <p className="prose">{t('atelier.lead')}</p>
      </header>

      <div className="atelier-layout">
        <section className="atelier-panel">
          <h2 className="section-label">{t('atelier.skeletonTitle')}</h2>
          <p className="params-lead">{t('atelier.skeletonLead')}</p>

          <div className="form-grid">
            <label>
              <span>{t('atelier.danceType')}</span>
              <select
                value={danceType}
                onChange={(e) => setDanceType(e.target.value as DanceType)}
              >
                <option value="tango">{t('atelier.dances.tango')}</option>
                <option value="milonga">{t('atelier.dances.milonga')}</option>
                <option value="vals">{t('atelier.dances.vals')}</option>
              </select>
            </label>

            <label>
              <span>{t('atelier.key')}</span>
              <select value={key} onChange={(e) => setKey(e.target.value)}>
                <option value="random">{t('atelier.random')}</option>
                {(options?.keys ?? []).map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>{t('atelier.progression')}</span>
              <select
                value={progressionId}
                onChange={(e) => setProgressionId(e.target.value)}
              >
                {progressionChoices.map((id) => (
                  <option key={id} value={id}>
                    {id === 'random' ? t('atelier.random') : id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>{t('atelier.form')}</span>
              <select value={formId} onChange={(e) => setFormId(e.target.value)}>
                {(options?.forms ?? [{ id: 'intro_aa_coda' }]).map((f) => (
                  <option key={f.id} value={f.id}>
                    {t(`atelier.forms.${f.id}`, { defaultValue: f.id })}
                  </option>
                ))}
                <option value="random">{t('atelier.random')}</option>
              </select>
            </label>

            <label>
              <span>{t('atelier.melodyDensity')}</span>
              <select
                value={melodyDensity}
                onChange={(e) => setMelodyDensity(e.target.value as MelodyLevel)}
              >
                {LEVELS.map((lv) => (
                  <option key={lv} value={lv}>
                    {levelLabel(lv)}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>{t('atelier.melodyVariation')}</span>
              <select
                value={melodyVariation}
                onChange={(e) =>
                  setMelodyVariation(e.target.value as MelodyLevel)
                }
              >
                {LEVELS.map((lv) => (
                  <option key={lv} value={lv}>
                    {levelLabel(lv)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="generator-actions">
            <button
              type="button"
              className="btn"
              disabled={busy}
              onClick={() => void onBuildSkeleton()}
            >
              {busy ? t('atelier.working') : t('atelier.build')}
            </button>
          </div>

          {skeleton && (
            <div className="skeleton-summary">
              <h3 className="params-subtitle">{t('atelier.skeletonSummary')}</h3>
              <dl className="params-grid">
                <div>
                  <dt>{t('atelier.key')}</dt>
                  <dd>{skeleton.key}</dd>
                </div>
                <div>
                  <dt>{t('atelier.progression')}</dt>
                  <dd className="mono">{skeleton.progression.join(' → ')}</dd>
                </div>
                <div>
                  <dt>{t('atelier.form')}</dt>
                  <dd>{skeleton.form.join(' → ')}</dd>
                </div>
                <div>
                  <dt>{t('atelier.bars')}</dt>
                  <dd>{skeleton.bars}</dd>
                </div>
                <div>
                  <dt>{t('atelier.melodyDensity')}</dt>
                  <dd>{levelLabel(skeleton.melody_density)}</dd>
                </div>
                <div>
                  <dt>{t('atelier.melodyVariation')}</dt>
                  <dd>{levelLabel(skeleton.melody_variation)}</dd>
                </div>
              </dl>
            </div>
          )}
        </section>

        <section className="atelier-panel atelier-render">
          <h2 className="section-label">{t('atelier.renderTitle')}</h2>
          <p className="params-lead">{t('atelier.renderLead')}</p>

          {!skeleton && <p className="status">{t('atelier.needSkeleton')}</p>}

          {skeleton && (
            <>
              <div className="style-chips" role="list">
                {(options?.render_styles ?? [
                  { id: 'simple', personality_type: 'neutral' },
                ]).map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    role="listitem"
                    className={
                      styleId === s.id ? 'style-chip active' : 'style-chip'
                    }
                    disabled={busy}
                    onClick={() => void onRenderStyle(s.id)}
                  >
                    {s.id !== 'simple' &&
                    'personality_emoji' in s &&
                    s.personality_emoji
                      ? `${s.personality_emoji} `
                      : ''}
                    {styleLabel(s.id)}
                  </button>
                ))}
              </div>

              <div className="instrument-toggles">
                <span className="instrument-toggles-label">
                  {t('atelier.instruments')}
                </span>
                {(
                  [
                    ['piano', t('params.instruments.piano')],
                    ['bandoneon', t('params.instruments.bandoneon')],
                    ['strings', t('params.instruments.strings')],
                  ] as const
                ).map(([id, label]) => (
                  <label key={id} className="instrument-toggle">
                    <input
                      type="checkbox"
                      checked={Boolean(instruments[id])}
                      disabled={busy || (id === 'piano' && styleId === 'simple')}
                      onChange={() => void onToggleInstrument(id)}
                    />
                    {label}
                  </label>
                ))}
              </div>

              <div className="generator-actions">
                {piece && !playing && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => void onPlay()}
                  >
                    {t('generator.play')}
                  </button>
                )}
                {playing && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={onStop}
                  >
                    {t('generator.stop')}
                  </button>
                )}
              </div>

              {piece && (
                <dl className="params-grid params-grid-result">
                  <div>
                    <dt>{t('atelier.rendering')}</dt>
                    <dd>{styleLabel(piece.orchestra_id)}</dd>
                  </div>
                  <div>
                    <dt>{t('generator.meta.rhythm')}</dt>
                    <dd>{piece.rhythm_pattern}</dd>
                  </div>
                  <div>
                    <dt>{t('atelier.decoration')}</dt>
                    <dd>
                      {piece.decoration != null
                        ? `${Math.round(piece.decoration * 100)}%`
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('generator.meta.bpm')}</dt>
                    <dd>{Math.round(piece.bpm)}</dd>
                  </div>
                  <div>
                    <dt>{t('generator.meta.duration')}</dt>
                    <dd>
                      {Math.round(piece.duration_seconds)}
                      {t('generator.seconds')}
                    </dd>
                  </div>
                </dl>
              )}
            </>
          )}
        </section>
      </div>

      {error && <p className="status status-error">{error}</p>}

      <p className="atelier-footnote prose">{t('atelier.disclaimer')}</p>
      <p className="atelier-footnote">
        <Link to="/orchestras">{t('atelier.browseOrchestras')}</Link>
      </p>
    </div>
  )
}
