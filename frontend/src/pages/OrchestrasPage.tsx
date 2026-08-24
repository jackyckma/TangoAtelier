import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { fetchOrchestras } from '../api'
import { useLocalized } from '../hooks/useLocalized'
import type { OrchestraCard, PersonalityType } from '../types'

const PERSONALITY_ORDER: PersonalityType[] = [
  'rhythmic',
  'lyrical',
  'smooth_powerful',
  'dramatic',
]

export function OrchestrasPage() {
  const { t } = useTranslation()
  const text = useLocalized()
  const [items, setItems] = useState<OrchestraCard[]>([])
  const [mode, setMode] = useState<'orchestra' | 'personality'>('orchestra')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchOrchestras()
      .then((data) => {
        if (!cancelled) {
          setItems(data)
          setError(null)
        }
      })
      .catch(() => {
        if (!cancelled) setError(t('orchestras.error'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [t])

  const grouped = useMemo(() => {
    const map = new Map<PersonalityType, OrchestraCard[]>()
    for (const type of PERSONALITY_ORDER) map.set(type, [])
    for (const item of items) {
      const list = map.get(item.personality_type) ?? []
      list.push(item)
      map.set(item.personality_type, list)
    }
    return map
  }, [items])

  return (
    <div className="page">
      <h1>{t('orchestras.title')}</h1>
      <p className="prose params-lead">{t('orchestras.subtitle')}</p>
      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'orchestra'}
          onClick={() => setMode('orchestra')}
        >
          {t('orchestras.byOrchestra')}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'personality'}
          onClick={() => setMode('personality')}
        >
          {t('orchestras.byPersonality')}
        </button>
      </div>

      {loading && <p className="status">{t('detail.loading')}</p>}
      {error && <p className="status">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="status">{t('orchestras.empty')}</p>
      )}

      {!loading && !error && mode === 'orchestra' && (
        <div className="orchestra-list">
          {items.map((item) => (
            <OrchestraLink key={item.id} item={item} text={text} t={t} />
          ))}
        </div>
      )}

      {!loading && !error && mode === 'personality' && (
        <>
          {PERSONALITY_ORDER.map((type) => {
            const group = grouped.get(type) ?? []
            if (group.length === 0) return null
            return (
              <section key={type} className="personality-block">
                <h2>
                  {group[0]?.personality_emoji} {t(`personality.${type}`)}
                </h2>
                <div className="orchestra-list">
                  {group.map((item) => (
                    <OrchestraLink key={item.id} item={item} text={text} t={t} />
                  ))}
                </div>
              </section>
            )
          })}
        </>
      )}
    </div>
  )
}

function OrchestraLink({
  item,
  text,
  t,
}: {
  item: OrchestraCard
  text: (v: OrchestraCard['name']) => string
  t: (key: string, opts?: Record<string, unknown>) => string
}) {
  return (
    <Link className="orchestra-row" to={`/orchestras/${item.id}`}>
      <span className="emoji" aria-hidden>
        {item.personality_emoji}
      </span>
      <span className="name">{text(item.name)}</span>
      <span className="meta">
        {t(`personality.${item.personality_type}`)} ·{' '}
        {t('orchestras.era', { start: item.era.start, end: item.era.end })}
      </span>
    </Link>
  )
}
