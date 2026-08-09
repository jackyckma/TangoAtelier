import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { fetchOrchestra } from '../api'
import { InlineGenerator } from '../components/InlineGenerator'
import { StyleDefaults } from '../components/StyleParams'
import { useLocalized } from '../hooks/useLocalized'
import type { OrchestraDetail } from '../types'

export function OrchestraDetailPage() {
  const { id = '' } = useParams()
  const { t } = useTranslation()
  const text = useLocalized()
  const [data, setData] = useState<OrchestraDetail | null>(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    fetchOrchestra(id)
      .then((detail) => {
        if (!cancelled) setData(detail)
      })
      .catch(() => {
        if (!cancelled) {
          setError(true)
          setData(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    if (!loading && data && window.location.hash === '#listen') {
      document.getElementById('listen')?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [loading, data])

  if (loading) {
    return (
      <div className="page">
        <p className="status">{t('detail.loading')}</p>
      </div>
    )
  }

  if (error || !data) {
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
    <div className="page detail-page">
      <Link className="back-link" to="/orchestras">
        ← {t('detail.back')}
      </Link>

      <div className="detail-layout">
        <header className="detail-header detail-span">
          <div className="eyebrow">
            {data.personality_emoji} {t(`personality.${data.personality_type}`)} ·{' '}
            {t('orchestras.era', { start: data.era.start, end: data.era.end })}
          </div>
          <h1>{text(data.name)}</h1>
        </header>

        <div className="detail-main">
          <p className="prose">{text(data.bio)}</p>
          <h2 className="section-label">{t('detail.sound')}</h2>
          <p className="prose">{text(data.sound_description)}</p>
        </div>

        <aside className="detail-aside">
          <InlineGenerator orchestraId={data.id} />
        </aside>

        <div className="detail-span">
          <StyleDefaults orchestra={data} />
          <h2 className="section-label">{t('detail.references')}</h2>
          <ul className="song-list">
            {data.reference_songs.map((song) => (
              <li key={`${song.title}-${song.type}`}>
                <span>{song.title}</span>
                <span className="type">{song.type}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
