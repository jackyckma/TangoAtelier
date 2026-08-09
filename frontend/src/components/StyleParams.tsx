import { useTranslation } from 'react-i18next'
import type { GeneratedPiece, OrchestraDetail } from '../types'

function LevelBar({ level }: { level: string }) {
  const map: Record<string, number> = {
    low: 1,
    medium: 2,
    high: 3,
    very_high: 4,
  }
  const n = map[level] ?? 2
  return (
    <span className="level-bar" aria-label={level}>
      {[1, 2, 3, 4].map((i) => (
        <span key={i} className={i <= n ? 'on' : ''} />
      ))}
    </span>
  )
}

export function StyleDefaults({ orchestra }: { orchestra: OrchestraDetail }) {
  const { t } = useTranslation()
  const h = orchestra.harmonic_tendencies
  const a = orchestra.articulation
  const [bpmLo, bpmHi] = orchestra.tempo_bpm_range

  return (
    <section className="style-params" aria-labelledby="style-defaults-title">
      <h2 className="section-label" id="style-defaults-title">
        {t('params.defaultsTitle')}
      </h2>
      <p className="prose params-lead">{t('params.defaultsLead')}</p>
      <dl className="params-grid">
        <div>
          <dt>{t('params.tempo')}</dt>
          <dd>
            {bpmLo}–{bpmHi} BPM
          </dd>
        </div>
        <div>
          <dt>{t('params.rhythm')}</dt>
          <dd>{orchestra.rhythm_patterns.join(' · ')}</dd>
        </div>
        <div>
          <dt>{t('params.mode')}</dt>
          <dd>{t(`params.modes.${h.primary_mode}`, { defaultValue: h.primary_mode })}</dd>
        </div>
        <div>
          <dt>{t('params.progressions')}</dt>
          <dd className="mono">{h.typical_progressions.join(', ')}</dd>
        </div>
        <div>
          <dt>{t('params.staccato')}</dt>
          <dd>
            <LevelBar level={a.staccato_level} />
            <span className="level-label">{t(`params.levels.${a.staccato_level}`, { defaultValue: a.staccato_level })}</span>
          </dd>
        </div>
        <div>
          <dt>{t('params.rubato')}</dt>
          <dd>
            <LevelBar level={a.rubato_level} />
            <span className="level-label">{t(`params.levels.${a.rubato_level}`, { defaultValue: a.rubato_level })}</span>
          </dd>
        </div>
        <div>
          <dt>{t('params.dynamics')}</dt>
          <dd>
            <LevelBar level={a.dynamic_contrast} />
            <span className="level-label">
              {t(`params.levels.${a.dynamic_contrast}`, { defaultValue: a.dynamic_contrast })}
            </span>
          </dd>
        </div>
        <div>
          <dt>{t('params.pauses')}</dt>
          <dd>
            <LevelBar level={a.pause_frequency} />
            <span className="level-label">
              {t(`params.levels.${a.pause_frequency}`, { defaultValue: a.pause_frequency })}
            </span>
          </dd>
        </div>
        <div>
          <dt>{t('params.borrowed')}</dt>
          <dd>
            <LevelBar level={h.borrowed_chords_frequency} />
            <span className="level-label">
              {t(`params.levels.${h.borrowed_chords_frequency}`, {
                defaultValue: h.borrowed_chords_frequency,
              })}
            </span>
          </dd>
        </div>
        <div>
          <dt>{t('params.dissonance')}</dt>
          <dd>
            <LevelBar level={h.dissonance_level} />
            <span className="level-label">
              {t(`params.levels.${h.dissonance_level}`, { defaultValue: h.dissonance_level })}
            </span>
          </dd>
        </div>
        <div>
          <dt>{t('params.voicing')}</dt>
          <dd>{t(`params.voicings.${h.voicing_style}`, { defaultValue: h.voicing_style })}</dd>
        </div>
        <div>
          <dt>{t('params.instrumentation')}</dt>
          <dd>
            {orchestra.instrumentation_defaults
              .map((inst) => t(`params.instruments.${inst}`, { defaultValue: inst }))
              .join(' · ')}
          </dd>
        </div>
      </dl>
    </section>
  )
}

export function GenerationResult({ piece }: { piece: GeneratedPiece }) {
  const { t } = useTranslation()
  return (
    <dl className="params-grid params-grid-result">
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
          <span className="meta-note">{t('generator.keyNote')}</span>
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
        <dt>{t('generator.meta.form')}</dt>
        <dd>{piece.form.join(' → ')}</dd>
      </div>
      <div>
        <dt>{t('generator.meta.seed')}</dt>
        <dd>{piece.seed}</dd>
      </div>
    </dl>
  )
}
