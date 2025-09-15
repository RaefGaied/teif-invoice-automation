import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Initialize i18next
i18n
    .use(Backend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        // Default language
        fallbackLng: 'en',
        // Enable debug only in development
        debug: process.env.NODE_ENV === 'development',
        // Allow keys to be phrases having `:`, ".", "," and "%"
        nsSeparator: false,
        keySeparator: false,
        // Don't escape content
        interpolation: {
            escapeValue: false,
        },
        // Namespaces to load by default
        ns: ['common', 'teif'],
        defaultNS: 'common',
        // Path to load translations from
        backend: {
            loadPath: '/locales/{{lng}}/{{ns}}.json',
        },
        // Language detection options
        detection: {
            order: ['localStorage', 'navigator'],
            caches: ['localStorage'],
        },
    });

export default i18n;
