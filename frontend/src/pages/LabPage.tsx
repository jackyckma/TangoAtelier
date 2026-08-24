import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  buildLabSkeleton,
  extendLabSkeleton,
  fetchLabOptions,
  renderLabLayer,
} from '../api'
import { ensureAudioReady, playNotes, stopPlayback } from '../audio/pianoPlayer'
import { ChordProgressionView } from '../components/ChordProgressionView'
import { useLocalized } from '../hooks/useLocalized'
import type {
  DanceType,
  GeneratedPiece,
  LabLayer,
  LabOptions,
  MelodyLevel,
  Skeleton,
} from '../types'

const LEVELS: MelodyLevel[] = ['low', 'medium', 'high']
const LAYERS: LabLayer[] = ['theme', 'groove', 'ensemble']

export function LabPage() {
  const { t, i18n } = useTranslation()
  const text = useLocalized()
  const [searchParams] = useSearchParams()
  const urlStyle = searchParams.get('style') || ''
  const urlTags = searchParams.get('tags')?.split(',').filter(Boolean) ?? []

  const [options, setOptions] = useState<LabOptions | null>(null)
  const [danceType, setDanceType] = useState<DanceType>('tango')
  const [mode, setMode] = useState('minor')
  const [progressionCharacter, setProgressionCharacter] = useState('diatonic')
  const [melodyDensity, setMelodyDensity] = useState<MelodyLevel>('medium')
  const [melodyVariation, setMelodyVariation] = useState<MelodyLevel>('medium')
  const [selectedTags, setSelectedTags] = useState<string[]>(urlTags)
  const [ensembleId, setEnsembleId] = useState('solo_piano')
  const [styleId, setStyleId] = useState(urlStyle || 'simple')
  const [layer, setLayer] = useState<LabLayer>('theme')
  const [skeleton, setSkeleton] = useState<Skeleton | null>(null)
  const [piece, setPiece] = useState<GeneratedPiece | null>(null)
  const [busy, setBusy] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [activeBar, setActiveBar] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchLabOptions()
      .then(setOptions)
      .catch(() => setError(t('lab.optionsError')))
    return () => stopPlayback()
  }, [t])

  useEffect(() => {
    if (urlStyle) setStyleId(urlStyle)
    if (urlTags.length) setSelectedTags(urlTags)
  }, [urlStyle, urlTags.join(',')])

  const tagLabel = (tagId: string) => {
    const tag = options?.intent_tags.find((x) => x.id === tagId)
    if (!tag) return tagId
    return i18n.language.startsWith('zh')
      ? `${tag.label_en} ${tag.label_zh}`
      : `${tag.label_en} · ${tag.label_zh}`
  }

  const toggleTag = (id: string) => {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const levelLabel = (level: MelodyLevel) => t(`lab.levels.${level}`)

  const translation = skeleton?.intent_translation ?? []

  const onBuild = async () => {
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    setActiveBar(null)
    setPiece(null)
    try {
      const sk = await buildLabSkeleton({
        dance_type: danceType,
        mode,
        progression_character: progressionCharacter,
        archetype_id: 'segment_song',
        melody_density: melodyDensity,
        melody_variation: melodyVariation,
        intent_tags: selectedTags.length ? selectedTags : undefined,
      })
      setSkeleton(sk)
      if (sk.suggested_ensemble_id) setEnsembleId(sk.suggested_ensemble_id)
      if (sk.suggested_style_id) setStyleId(sk.suggested_style_id)
      setLayer('theme')
      const rendered = await renderLabLayer(sk, 'theme', {
        ensemble_id: ensembleId,
        style_id: 'simple',
      })
      setPiece(rendered)
    } catch {
      setError(t('lab.buildError'))
    } finally {
      setBusy(false)
    }
  }

  const onRenderLayer = async (nextLayer: LabLayer) => {
    if (!skeleton) return
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    setActiveBar(null)
    setLayer(nextLayer)
    try {
      const rendered = await renderLabLayer(skeleton, nextLayer, {
        ensemble_id: ensembleId,
        style_id: nextLayer === 'ensemble' ? styleId : 'simple',
      })
      setPiece(rendered)
    } catch {
      setError(t('lab.renderError'))
    } finally {
      setBusy(false)
    }
  }

  const onExtend = async () => {
    if (!skeleton) return
    setBusy(true)
    setError(null)
    stopPlayback()
    setPlaying(false)
    setActiveBar(null)
    try {
      const sk = await extendLabSkeleton({
        seed: skeleton.seed,
        dance_type: skeleton.dance_type,
        mode: skeleton.mode,
        progression_character:
          skeleton.progression_character || progressionCharacter,
        melody_density: skeleton.melody_density,
        melody_variation: skeleton.melody_variation,
        intent_tags: selectedTags.length ? selectedTags : undefined,
        generation_options: skeleton.generation_options,
      })
      setSkeleton(sk)
      const rendered = await renderLabLayer(sk, layer, {
        ensemble_id: ensembleId,
        style_id: layer === 'ensemble' ? styleId : 'simple',
      })
      setPiece(rendered)
    } catch {
      setError(t('lab.extendError'))
    } finally {
      setBusy(false)
    }
  }

  const onPlay = async () => {
    if (!piece) return
    try {
      await ensureAudioReady()
      setPlaying(true)
      setActiveBar(0)
      const beats = piece.time_signature[0] || 2
      const barDurationSeconds = (60 / piece.bpm) * beats
      await playNotes(piece.notes, {
        barDurationSeconds,
        bars: piece.bars,
        onBar: (bar) => setActiveBar(bar),
        onEnded: () => {
          setPlaying(false)
          setActiveBar(null)
        },
      })
    } catch {
      setPlaying(false)
      setActiveBar(null)
      setError(t('generator.audioError'))
    }
  }

  const onStop = () => {
    stopPlayback()
    setPlaying(false)
    setActiveBar(null)
  }

  const ensembleLabel = useMemo(() => {
    const p = options?.ensemble_presets.find((x) => x.id === ensembleId)
    return p ? text(p.label) : ensembleId
  }, [ensembleId, options, text])

  const styleLabel = (id: string) => {
    if (id === 'simple') return t('lab.simpleStyle')
    const s = options?.style_references.find((x) => x.id === id)
    return s?.name ? text(s.name) : id
  }

  return (
    <div className="page atelier-page lab-page">
      <header className="detail-header">
        <div className="eyebrow">{t('lab.eyebrow')}</div>
        <h1>{t('lab.title')}</h1>
        <p className="prose">{t('lab.lead')}</p>
      </header>

      <div className="atelier-layout">
        <section className="atelier-panel">
          <h2 className="section-label">{t('lab.shapeTitle')}</h2>
          <p className="params-lead">{t('lab.shapeLead')}</p>

          <div className="lab-tags" role="group" aria-label={t('lab.tagsLabel')}>
            {(options?.intent_tags ?? []).map((tag) => (
              <button
                key={tag.id}
                type="button"
                className={
                  selectedTags.includes(tag.id)
                    ? 'style-chip active'
                    : 'style-chip'
                }
                onClick={() => toggleTag(tag.id)}
              >
                {tagLabel(tag.id)}
              </button>
            ))}
          </div>

          {translation.length > 0 && (
            <div className="lab-translation">
              <h3 className="params-subtitle">{t('lab.translationTitle')}</h3>
              <ul className="lab-translation-list">
                {translation.map((row) => (
                  <li key={row.tag_id}>
                    <strong>{row.label_en}</strong> · {row.label_zh}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="form-grid">
            <label>
              <span>{t('lab.danceType')}</span>
              <select
                value={danceType}
                onChange={(e) => setDanceType(e.target.value as DanceType)}
              >
                <option value="tango">{t('lab.dances.tango')}</option>
                <option value="milonga">{t('lab.dances.milonga')}</option>
                <option value="vals">{t('lab.dances.vals')}</option>
              </select>
            </label>
            <label>
              <span>{t('lab.mode')}</span>
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                {(options?.modes ?? []).map((m) => (
                  <option key={m.id} value={m.id}>
                    {text(m.label)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>{t('lab.progressionCharacter')}</span>
              <select
                value={progressionCharacter}
                onChange={(e) => setProgressionCharacter(e.target.value)}
              >
                {(options?.progression_characters ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {text(p.label)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>{t('lab.melodyDensity')}</span>
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
              <span>{t('lab.melodyVariation')}</span>
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
              onClick={() => void onBuild()}
            >
              {busy ? t('lab.working') : t('lab.build')}
            </button>
          </div>

          {skeleton && (
            <div className="skeleton-summary">
              <h3 className="params-subtitle">{t('lab.skeletonSummary')}</h3>
              <dl className="params-grid">
                <div>
                  <dt>{t('lab.mode')}</dt>
                  <dd>
                    {skeleton.key} ({skeleton.mode})
                  </dd>
                </div>
                <div>
                  <dt>{t('lab.bars')}</dt>
                  <dd>
                    {skeleton.bars}
                    {skeleton.archetype_id === 'segment_song' && (
                      <span className="params-lead"> · {t('lab.segmentNote')}</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt>{t('lab.progressionCharacter')}</dt>
                  <dd className="mono">{skeleton.progression.join(' → ')}</dd>
                </div>
                <div>
                  <dt>{t('lab.seed')}</dt>
                  <dd className="mono">{skeleton.seed}</dd>
                </div>
              </dl>
              <div className="generator-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={busy || skeleton.archetype_id === 'classic_dance'}
                  onClick={() => void onExtend()}
                >
                  {t('lab.extend')}
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="atelier-panel atelier-render">
          <h2 className="section-label">{t('lab.layersTitle')}</h2>
          <p className="params-lead">{t('lab.layersLead')}</p>

          {!skeleton && <p className="status">{t('lab.needSkeleton')}</p>}

          {skeleton && (
            <>
              <div className="style-chips" role="tablist">
                {LAYERS.map((lv) => (
                  <button
                    key={lv}
                    type="button"
                    role="tab"
                    aria-selected={layer === lv}
                    className={layer === lv ? 'style-chip active' : 'style-chip'}
                    disabled={busy}
                    onClick={() => void onRenderLayer(lv)}
                  >
                    {t(`lab.layers.${lv}`)}
                  </button>
                ))}
              </div>

              {layer === 'ensemble' && (
                <>
                  <div className="form-grid">
                    <label>
                      <span>{t('lab.ensemble')}</span>
                      <select
                        value={ensembleId}
                        onChange={(e) => setEnsembleId(e.target.value)}
                      >
                        {(options?.ensemble_presets ?? []).map((p) => (
                          <option key={p.id} value={p.id}>
                            {text(p.label)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>{t('lab.styleReference')}</span>
                      <select
                        value={styleId}
                        onChange={(e) => setStyleId(e.target.value)}
                      >
                        <option value="simple">{t('lab.simpleStyle')}</option>
                        {(options?.style_references ?? []).map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.personality_emoji ? `${s.personality_emoji} ` : ''}
                            {s.name ? text(s.name) : s.id}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={busy}
                    onClick={() => void onRenderLayer('ensemble')}
                  >
                    {t('lab.applyEnsemble')}
                  </button>
                </>
              )}

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
                <>
                  <dl className="params-grid params-grid-result">
                    <div>
                      <dt>{t('lab.currentLayer')}</dt>
                      <dd>{t(`lab.layers.${layer}`)}</dd>
                    </div>
                    <div>
                      <dt>{t('lab.ensemble')}</dt>
                      <dd>{ensembleLabel}</dd>
                    </div>
                    {layer === 'ensemble' && (
                      <div>
                        <dt>{t('lab.styleReference')}</dt>
                        <dd>{styleLabel(piece.orchestra_id)}</dd>
                      </div>
                    )}
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
                  <ChordProgressionView piece={piece} activeBar={activeBar} />
                </>
              )}
            </>
          )}
        </section>
      </div>

      {error && <p className="status status-error">{error}</p>}

      <p className="atelier-footnote prose">{t('lab.disclaimer')}</p>
      <p className="atelier-footnote">
        <Link to="/orchestras">{t('lab.browseReference')}</Link>
      </p>
    </div>
  )
}
