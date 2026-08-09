import { useTranslation } from 'react-i18next'
import type { Localized } from '../types'

export function useLocalized() {
  const { i18n } = useTranslation()
  const lang = i18n.language.startsWith('zh') ? 'zh' : 'en'
  return (value: Localized) => value[lang] || value.en || value.zh
}
