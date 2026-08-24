import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export function HomePage() {
  const { t } = useTranslation()

  return (
    <section className="hero">
      <div className="hero-inner">
        <p className="hero-brand">{t('brand')}</p>
        <h1>{t('home.headline')}</h1>
        <p>{t('home.lead')}</p>
        <div className="hero-actions">
          <Link className="btn" to="/lab">
            {t('home.ctaLab')}
          </Link>
          <Link className="btn btn-ghost" to="/orchestras">
            {t('home.ctaReference')}
          </Link>
          <span className="hero-note">{t('home.note')}</span>
        </div>
      </div>
    </section>
  )
}
