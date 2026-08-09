import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  zh: {
    translation: {
      brand: 'TangoAtelier',
      nav: {
        home: '首頁',
        orchestras: '樂團',
      },
      home: {
        headline: '用可解釋的音樂，學探戈的節奏指紋',
        lead: '認識黃金時代樂團風格，透過原創生成與 Hint，在鋼琴或吉他上練習即興。',
        cta: '瀏覽樂團',
        note: '不播放原曲——只生成教學用的原創音樂。',
      },
      orchestras: {
        title: '樂團總覽',
        byOrchestra: '依樂團',
        byPersonality: '依性格',
        empty: '暫時沒有樂團資料。',
        error: '無法載入樂團列表。請確認後端已啟動。',
        era: '{{start}}–{{end}}',
      },
      personality: {
        rhythmic: '節奏系',
        lyrical: '柔情系',
        smooth_powerful: '氣勢系',
        dramatic: '戲劇系',
      },
      detail: {
        back: '返回列表',
        sound: '聽起來像什麼',
        references: '代表曲目（僅作教育參考，不提供原曲播放）',
        generateSoon: '生成此風格音樂（Phase 1）',
        loading: '載入中…',
        error: '找不到這個樂團。',
      },
      lang: {
        zh: '中',
        en: 'EN',
      },
    },
  },
  en: {
    translation: {
      brand: 'TangoAtelier',
      nav: {
        home: 'Home',
        orchestras: 'Orchestras',
      },
      home: {
        headline: 'Learn tango’s rhythmic fingerprints through explainable music',
        lead: 'Study Golden Age orchestra styles, then practise improvisation on piano or guitar with original generations and visual hints.',
        cta: 'Browse orchestras',
        note: 'No copyrighted recordings—only original music generated for learning.',
      },
      orchestras: {
        title: 'Orchestras',
        byOrchestra: 'By orchestra',
        byPersonality: 'By personality',
        empty: 'No orchestras yet.',
        error: 'Could not load orchestras. Is the API running?',
        era: '{{start}}–{{end}}',
      },
      personality: {
        rhythmic: 'Rhythmic',
        lyrical: 'Lyrical',
        smooth_powerful: 'Smooth & powerful',
        dramatic: 'Dramatic',
      },
      detail: {
        back: 'Back to list',
        sound: 'What it sounds like',
        references: 'Reference titles (educational list only—no original playback)',
        generateSoon: 'Generate this style (Phase 1)',
        loading: 'Loading…',
        error: 'Orchestra not found.',
      },
      lang: {
        zh: '中',
        en: 'EN',
      },
    },
  },
}

void i18n.use(initReactI18next).init({
  resources,
  lng: 'zh',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
