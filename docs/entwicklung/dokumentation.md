# Dokumentation bearbeiten

Die Dokumentation liegt im Repository unter `docs/`. Die VitePress-Site ist die maßgebliche Fassung; die früheren Markdown-Dateien im Repository-Root enthalten nur noch Verweise. Zum Arbeiten an der Doku muss die Health-Coach-Anwendung nicht laufen.

## Lokal starten

Node.js 24 gemäß `.nvmrc` verwenden und im Repository-Root ausführen:

```bash
make docs-build
make docs-dev
```

Der Befehl installiert fehlende Abhängigkeiten automatisch und startet die Site unter **http://127.0.0.1:5174/**. Das Terminal geöffnet lassen; Änderungen an den Markdown-Seiten werden direkt übernommen. Der Dokumentationsserver verwendet einen eigenen Port neben dem React-Frontend. Für einen Produktions-Build:

```bash
make docs-build
make docs-preview
```

Die lokale Vorschau des Builds ist unter **http://127.0.0.1:4174/** erreichbar. Der statische Build liegt unter `docs/.vitepress/dist/`. Dieser Build gehört zur **Projektseite**, nicht zum React-Frontend der Trainingsanwendung unter `frontend/dist/`.

Ohne Make funktionieren `cd docs && npm ci && npm run dev`. Wenn eine vorhandene Installation beschädigt ist, im `docs/`-Ordner `npm ci` erneut ausführen.

## Wo steht was?

| Thema | Ort |
|---|---|
| Überblick und arc42-Kapitel 1–12 | [`docs/architektur/`](/architektur/) |
| Historische Funktionsliste und Architekturregeln | [Anhänge](/architektur/anhaenge) |
| Debian, systemd, Caddy, Provisionierung | [Deployment und Betrieb](/betrieb/deployment) |
| Lokales LLM und Modellbetrieb | [Lokales LLM](/betrieb/lokales-llm) |
| Windows-/Linux-Entwicklungsumgebung | [Entwicklungsumgebung](/entwicklung/einrichten) |
| WebSocket-Verträge | [Schnittstellen](/schnittstellen/websockets) |

Neue Seiten in `docs/.vitepress/config.mts` in Navigation und Sidebar eintragen. Bei Architekturänderungen den tatsächlichen Implementierungsstand und mögliche Risiken aktualisieren; Beispiele und Befehle gegen die passenden Make-Targets beziehungsweise Deploy-Skripte prüfen. Site-Build vor dem Einchecken ausführen.

Die Dokumentations-Site wird separat erstellt. `deploy/provision.sh` baut weiterhin ausschließlich die Trainingsanwendung und ändert weder Caddy-Routen noch den Kiosk-Start für diese Site.

## GitHub Pages

Der Workflow `.github/workflows/docs-pages.yml` baut die Site bei Änderungen an `docs/` auf dem Standardbranch und veröffentlicht `docs/.vitepress/dist/` über GitHub Pages. Er kann auch manuell über **Actions → Publish documentation** gestartet werden, sofern der Standardbranch ausgewählt ist. Der Build setzt den VitePress-Basispfad aus dem Repository-Namen; für `engel-b/coach` lautet die Adresse nach Aktivierung voraussichtlich `https://engel-b.github.io/coach/`.

Vor der ersten Veröffentlichung unter **Settings → Pages → Build and deployment → Source** die Option **GitHub Actions** wählen. Falls GitHub Pages für das Repository beziehungsweise den Tarif nicht verfügbar ist, wird der Job nicht erfolgreich veröffentlichen. GitHub Pages kann eine Site auch aus einem privaten Repository öffentlich erreichbar machen; die Sichtbarkeit in den Pages-Einstellungen vor dem Aktivieren prüfen. Keine Geheimnisse oder personenbezogenen Trainingsdaten in die Dokumentation aufnehmen.
