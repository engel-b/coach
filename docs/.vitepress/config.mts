import { defineConfig } from 'vitepress'

export default defineConfig({
  base: process.env.DOCS_BASE || '/',
  lang: 'de-DE',
  title: 'Health Coach',
  description: 'Architektur, Entwicklung und Betrieb des lokalen Fitness-Coachs',
  cleanUrls: true,
  lastUpdated: true,
  head: [
    ['meta', { name: 'theme-color', content: '#10232b' }],
  ],
  themeConfig: {
    logo: '/mark.svg',
    siteTitle: 'Health Coach',
    nav: [
      { text: 'Start', link: '/' },
      { text: 'Architektur', link: '/architektur/' },
      { text: 'Entwicklung', link: '/entwicklung/einrichten' },
      { text: 'Betrieb', link: '/betrieb/deployment' },
      { text: 'Schnittstellen', link: '/schnittstellen/websockets' },
    ],
    sidebar: {
      '/architektur/': [
        { text: 'Architektur nach arc42', items: [
          { text: 'Überblick und Status', link: '/architektur/' },
          { text: '01 · Einführung und Ziele', link: '/architektur/01-einfuehrung-und-ziele' },
          { text: '02 · Randbedingungen', link: '/architektur/02-randbedingungen' },
          { text: '03 · Kontextabgrenzung', link: '/architektur/03-kontextabgrenzung' },
          { text: '04 · Lösungsstrategie', link: '/architektur/04-loesungsstrategie' },
          { text: '05 · Bausteinsicht', link: '/architektur/05-bausteinsicht' },
          { text: '06 · Laufzeitsicht', link: '/architektur/06-laufzeitsicht' },
          { text: '07 · Verteilungssicht', link: '/architektur/07-verteilungssicht' },
          { text: '08 · Querschnittliche Konzepte', link: '/architektur/08-querschnittliche-konzepte' },
          { text: '09 · Architekturentscheidungen', link: '/architektur/09-architekturentscheidungen' },
          { text: '10 · Qualitätsanforderungen', link: '/architektur/10-qualitaetsanforderungen' },
          { text: '11 · Risiken und technische Schulden', link: '/architektur/11-risiken' },
          { text: '12 · Glossar', link: '/architektur/12-glossar' },
          { text: 'Anhänge', link: '/architektur/anhaenge' },
        ] },
      ],
      '/entwicklung/': [
        { text: 'Entwicklung', items: [
          { text: 'Umgebung einrichten', link: '/entwicklung/einrichten' },
          { text: 'Dokumentation bearbeiten', link: '/entwicklung/dokumentation' },
        ] },
      ],
      '/betrieb/': [
        { text: 'Betrieb', items: [
          { text: 'Deployment und Betrieb', link: '/betrieb/deployment' },
          { text: 'Lokales LLM', link: '/betrieb/lokales-llm' },
        ] },
      ],
      '/schnittstellen/': [
        { text: 'Schnittstellen', items: [
          { text: 'WebSocket-Verträge', link: '/schnittstellen/websockets' },
        ] },
      ],
    },
    search: { provider: 'local' },
    outline: { level: [2, 3], label: 'Auf dieser Seite' },
    docFooter: { prev: 'Vorherige Seite', next: 'Nächste Seite' },
    returnToTopLabel: 'Nach oben',
    sidebarMenuLabel: 'Menü',
    darkModeSwitchLabel: 'Darstellung',
    lightModeSwitchTitle: 'Helles Design',
    darkModeSwitchTitle: 'Dunkles Design',
    lastUpdatedText: 'Zuletzt geändert',
  },
})
