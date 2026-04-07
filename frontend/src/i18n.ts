import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'
import { safeStorageGet } from './utils/resilience'

const storedLocale = safeStorageGet('locale')
const locale = storedLocale === 'en' ? 'en' : 'zh'

const i18n = createI18n({
  legacy: false,
  locale,
  fallbackLocale: 'en',
  messages: {
    zh,
    en
  }
})

export default i18n
