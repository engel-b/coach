---
layout: home
title: Health Coach
hero:
  name: Health Coach
  text: Lokal trainieren. Entscheidungen verstehen.
  tagline: Die Projektdokumentation für Architektur, Entwicklung und Betrieb eines lokalen Fitness-Coachs.
  image:
    src: /mark.svg
    alt: Health Coach Symbol
  actions:
    - theme: brand
      text: Architektur entdecken
      link: /architektur/
    - theme: alt
      text: Entwicklungsumgebung einrichten
      link: /entwicklung/einrichten
features:
  - title: Architektur nach arc42
    details: Systemkontext, Bausteine, Laufzeitszenarien und Entscheidungen in zwölf Kapiteln.
    link: /architektur/
    linkText: Zur Architektur
  - title: Lokal und nachvollziehbar
    details: Deterministische Trainingsempfehlung und Live-Coaching; lokale Sprache und ein optionales LLM ergänzen die Fachlogik.
    link: /architektur/04-loesungsstrategie
    linkText: Zur Lösungsstrategie
  - title: Von Entwicklung bis Betrieb
    details: Schrittweise Anleitungen für Windows und Linux sowie Debian-Appliance, systemd und Fehlersuche.
    link: /betrieb/deployment
    linkText: Zum Betrieb
---

## Einstieg

Health Coach kombiniert Check-ins, individuelle Trainingsempfehlungen, strukturierte Workouts, optionale BLE-Telemetrie und Live-Coaching. Die fachlichen Entscheidungen bleiben deterministisch; ein lokales LLM darf Texte formulieren, aber die Trainingsentscheidung nicht ändern.

- [Architektur und aktueller Stand](/architektur/)
- [Entwicklungsumgebung einrichten](/entwicklung/einrichten)
- [Deployment und Betrieb](/betrieb/deployment)
- [WebSocket-Schnittstellen](/schnittstellen/websockets)

Die Site wird aus Markdown im Repository gebaut. Hinweise zum Bearbeiten und Prüfen stehen unter [Dokumentation bearbeiten](/entwicklung/dokumentation).
