import { NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export function Layout() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language.startsWith('zh') ? 'zh' : 'en'

  return (
    <div className="shell">
      <header className="site-nav">
        <NavLink to="/" className="brand">
          {t('brand')}
        </NavLink>
        <nav className="nav-links" aria-label="primary">
          <NavLink to="/" end>
            {t('nav.home')}
          </NavLink>
          <NavLink to="/lab">{t('nav.lab')}</NavLink>
          <NavLink to="/orchestras">{t('nav.reference')}</NavLink>
          <div className="lang-toggle" role="group" aria-label="language">
            <button
              type="button"
              aria-pressed={lang === 'zh'}
              onClick={() => void i18n.changeLanguage('zh')}
            >
              {t('lang.zh')}
            </button>
            <button
              type="button"
              aria-pressed={lang === 'en'}
              onClick={() => void i18n.changeLanguage('en')}
            >
              {t('lang.en')}
            </button>
          </div>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
