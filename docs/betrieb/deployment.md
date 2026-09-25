# Health Coach – Deployment und Betrieb unter Debian

## 1. Zweck dieses Dokuments

Dieses Dokument beschreibt das Deployment und den Betrieb des **Health Coach** auf dem Debian-Produktivsystem.

Es dokumentiert:

- die beteiligten systemd-Services,
- deren Startreihenfolge und Abhängigkeiten,
- die erforderlichen Environment-Konfigurationen,
- die Aufgaben von `provision.sh` und `prepare.sh`,
- den Update-Ablauf,
- den normalen Boot-Ablauf,
- die Verantwortlichkeiten der einzelnen Komponenten,
- die erforderlichen Installations-, Prüf- und Betriebsbefehle,
- die Einbindung des lokalen LLM über `llama-server`.

Ziel ist ein Appliance-artiger Betrieb. Nach einer erfolgreichen Provisionierung soll das System ohne Entwicklungswerkzeuge und ohne Netzwerkzugriff normal starten können. Das lokale LLM ist eine optionale Zusatzfunktion; ein Ausfall des LLM darf API und Kernfunktionen nicht blockieren.

---

## 2. Zielverzeichnisse

Die Anwendung wird unter folgendem Pfad betrieben:

```text
/opt/health-coach
```

Relevante Verzeichnisse:

```text
/opt/health-coach/
├── backend/
│   ├── .venv/
│   └── ...
├── data/
│   ├── db/
│   |   └── health-coach.db
│   └── models/
│   |   ├── llm/
│   │   |   └── qwen3.5-0.8b-q4_0.gguf
│   |   ├── piper-tts/
│   |   |   ├── de_DE-thorsten-medium.onnx
│   |   |   └── de_DE-thorsten-medium.onnx.json
│   └── videos/
├── frontend/
│   └── ...
└── deploy/
    ├── provision.sh
    ├── prepare.sh
    └── ...
```

Systemweite Konfiguration:

```text
/etc/health-coach/
├── backend.env
└── llm.env
```

systemd-Units:

```text
/etc/systemd/system/
├── health-coach-prepare.service
├── health-coach-api.service
├── health-coach-device-agent.service
└── health-coach-llm.service
```

Das gebaute Frontend wird **nicht** durch einen eigenen Health-Coach-Frontend-Service ausgeliefert. Caddy liefert `frontend/dist` statisch aus und übernimmt gleichzeitig den Reverse Proxy zu FastAPI. Chromium läuft in der grafischen Kiosk-Sitzung.

---

## 3. Komponenten und Verantwortlichkeiten

### 3.1 `provision.sh`

`deploy/provision.sh` ist das **explizite Update- und Deployment-Skript**.

Es wird nicht bei jedem normalen Boot ausgeführt.

Verantwortlichkeiten:

1. Remote-Refs aktualisieren (`git fetch --prune origin`). Optional angegebenen Zielbranch nur verwenden, wenn `origin/<branch>` existiert; anschließend `git switch` und `git pull --ff-only`. Ohne Zielbranch bleibt der aktuelle Branch aktiv.
2. Nach erfolgreichem Pull `cleanup-branches.sh` aufrufen und anschließend aktuellen Branch und Commit ausgeben.
3. Python Virtual Environment anlegen, falls erforderlich.
4. Backend-Abhängigkeiten installieren bzw. aktualisieren.
5. TTS-Modell/-Stimme provisionieren.
6. LLM-Modell provisionieren.
7. Node.js 24 LTS prüfen (mindestens 24.15.0; getestete Version siehe `.nvmrc`).
8. Frontend-Abhängigkeiten reproduzierbar mit `npm ci` installieren.
9. Frontend bauen.
10. Laufzeitdatenverzeichnisse unter `data/` sicherstellen und bekannte Altpfade einmalig migrieren.
11. `/etc/health-coach/backend.env` und `/etc/health-coach/llm.env` gegen die Repo-Vorlagen abgleichen. Fehlende bzw. veraltete Schlüssel werden interaktiv zur Ergänzung/Entfernung angeboten; bestehende Werte bleiben erhalten.
12. systemd-Units gegen die Repo-Vorlagen vergleichen und Änderungen nach Rückfrage installieren.
13. Datenbankschema mit Alembic aktualisieren.
14. Health-Coach-Services neu starten.
15. `/etc/caddy/Caddyfile` gegen die Repo-Vorlage vergleichen, optional aktualisieren, mit `caddy validate` prüfen und Caddy nur bei erfolgreicher Validierung neu starten.
16. Fehler sichtbar abbrechen, statt eine teilweise installierte Version weiterzustarten.

`provision.sh` darf:

- Netzwerk verwenden,
- Dateien herunterladen,
- Paketmanager ausführen,
- Builds durchführen,
- längere Zeit benötigen.

Typischer Aufruf:

```bash
cd /opt/health-coach
./deploy/provision.sh
```

Optional kann ein Remote-Branch gewählt werden:

```bash
./deploy/provision.sh --branch feature/mein-branch
# alternativ als Kurzform:
./deploy/provision.sh feature/mein-branch
```

Der Branch wird erst nach `git fetch --prune origin` akzeptiert, wenn er auf `origin` existiert.

Die Konfigurationsabgleiche sind absichtlich interaktiv. Für eine bewusst vollautomatische Aktualisierung können alle Rückfragen mit `--yes` bestätigt werden:

```bash
./deploy/provision.sh --yes
```

Vor Änderungen unter `/etc` legt das Skript Sicherungen mit Zeitstempel (`*.bak.YYYYMMDD-HHMMSS`) an.

Ein Reboot ist nach einem erfolgreichen Update grundsätzlich nicht erforderlich.

---

### 3.2 `prepare.sh`

`deploy/prepare.sh` ist die **Boot-Vorbereitung**.

Es wird durch `health-coach-prepare.service` bei einem normalen Systemstart ausgeführt. Das aktuelle `provision.sh` führt die Alembic-Migration im Update-Ablauf ebenfalls explizit aus und startet anschließend den Prepare-Service neu; der normale Boot bleibt davon getrennt.

Verantwortlichkeiten:

1. Prüfen, ob die bereits provisionierte Installation grundsätzlich vorhanden ist.
2. Lokale Runtime-Voraussetzungen prüfen bzw. vorbereiten.
3. Datenbankschema mit Alembic auf den Stand des installierten Codes bringen.

`prepare.sh` darf beim normalen Boot **nicht**:

- `git pull` ausführen,
- Python-Pakete herunterladen,
- `npm ci` ausführen,
- das Frontend bauen,
- TTS-Modelle herunterladen,
- LLM-Modelle herunterladen,
- von einer Internetverbindung abhängig sein.

Ein minimaler Inhalt ist beispielsweise:

```bash
#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PYTHON="${BACKEND_DIR}/.venv/bin/python"

echo "=== Health Coach: preparing runtime ==="

if [ ! -x "${PYTHON}" ]; then
    echo "ERROR: Python virtual environment is missing."
    echo "Run deploy/provision.sh first."
    exit 1
fi

echo "Applying database migrations ..."
cd "${BACKEND_DIR}"
"${PYTHON}" -m alembic upgrade head

echo "=== Health Coach: runtime ready ==="
```

Die Migration wird bewusst auch beim Boot ausgeführt. Ist das Schema bereits aktuell, nimmt `alembic upgrade head` keine weitere Schemaänderung vor.

---

## 4. Unterschied zwischen `provision.sh` und `prepare.sh`

| Thema | `provision.sh` | `prepare.sh` |
|---|---|---|
| Zweck | Update / Deployment | Runtime-Vorbereitung beim Boot |
| Aufruf | manuell | automatisch durch systemd beim Boot bzw. bei explizitem Service-Restart |
| `git pull` | ja | nein |
| Netzwerk erlaubt | ja | nein |
| Python-Dependencies | installieren/aktualisieren | nein |
| `npm ci` | ja | nein |
| Frontend-Build | ja | nein |
| TTS-Modell | provisionieren | nur vorhandenen Stand verwenden |
| LLM-Modell | provisionieren | nur vorhandenen Stand verwenden |
| Alembic-Migration | ja, im Update-Ablauf | ja |
| Services neu starten | ja | nein |
| Muss schnell sein | nicht zwingend | ja |
| Muss offline funktionieren | nein | ja |

Kurz gesagt:

```text
provision.sh
    = "Installiere/deploye diesen Git-Stand."

prepare.sh
    = "Bereite die bereits installierte Version für diesen Boot vor."
```

---

## 5. Ablaufdiagramme

### 5.1 Update-Ablauf

```text
Administrator
     |
     v
deploy/provision.sh
     |
     +--> git fetch --prune origin
     |
     +--> optional Remote-Branch prüfen / git switch
     |
     +--> git pull --ff-only
     |
     +--> cleanup-branches.sh
     |
     +--> Branch + Commit ausgeben
     |
     +--> Python venv / Backend Dependencies
     |
     +--> TTS-Modell prüfen/provisionieren
     |
     +--> LLM-Modell prüfen/provisionieren
     |
     +--> npm ci
     |
     +--> Frontend Build
     |
     +--> prepare.sh
     |      |
     |      +--> Alembic upgrade head
     |
     +--> systemctl daemon-reload
     |
     +--> Services neu starten
     |
     v
Neue Version aktiv
```

Der Git-Abschnitt in `provision.sh` folgt diesem Ablauf:

```text
git fetch --prune origin
    -> optional: existiert origin/<branch>?
    -> optional: git switch <branch> (ggf. Tracking-Branch anlegen)
    -> git pull --ff-only
    -> cleanup-branches.sh
```

Ohne Branchparameter wird der aktuelle Branch nach dem Fetch weiterverwendet. Ein nicht auf `origin` vorhandener Zielbranch führt vor dem Switch zum Abbruch. `--ff-only` verhindert, dass das Produktivsystem bei divergierenden Git-Ständen automatisch einen Merge erzeugt.

### 5.2 Normaler Boot-Ablauf

Beim normalen Systemstart wird **kein Update** durchgeführt.

```text
Debian Boot
    |
    v
health-coach-prepare.service
    |
    |  lokale Prüfung
    |  Alembic-Migration
    |
    +-----------------------------+
    |                             |
    v                             v
health-coach-llm.service    health-coach-api.service
                                  |
                                  v
                        health-coach-device-agent.service
```

Caddy wird als eigener Systemdienst gestartet und verwendet das bereits durch `provision.sh` gebaute `frontend/dist`. Chromium startet anschließend in der grafischen Kiosk-Sitzung.

---

## 6. Abhängigkeitsmodell

```text
prepare
  |
  +-------------------+
  |                   |
  v                   v
LLM                  API
                      |
                      v
                 Device Agent
```

Für das LLM gilt:

```text
LLM verfügbar
    -> API kann lokale LLM-Funktionen verwenden

LLM nicht verfügbar
    -> API läuft weiter
    -> deterministischer Fallback bleibt verfügbar
```

Deshalb verwendet die API:

```ini
Wants=health-coach-llm.service
```

und absichtlich **nicht**:

```ini
Requires=health-coach-llm.service
```

`prepare` ist dagegen eine harte Voraussetzung für API und LLM.

---

## 7. systemd-Konfigurationen

### 7.1 `health-coach-prepare.service`

Datei:

```text
/etc/systemd/system/health-coach-prepare.service
```

```ini
[Unit]
Description=Prepare Health Coach
After=local-fs.target
Before=health-coach-llm.service health-coach-api.service

[Service]
Type=oneshot
User=coach
Group=coach

WorkingDirectory=/opt/health-coach
ExecStart=/opt/health-coach/deploy/prepare.sh

RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Verantwortung:

- lokale Runtime vorbereiten,
- Datenbankmigrationen ausführen,
- bei einem nicht provisionierten System sauber fehlschlagen.

### 7.2 `health-coach-llm.service`

Datei:

```text
/etc/systemd/system/health-coach-llm.service
```

```ini
[Unit]
Description=Health Coach Local LLM
After=health-coach-prepare.service
Requires=health-coach-prepare.service

[Service]
Type=simple
User=coach
Group=coach

WorkingDirectory=/opt/health-coach
EnvironmentFile=/etc/health-coach/llm.env

ExecStart=/usr/local/bin/llama-server \
    -m ${HEALTH_COACH_LLM_MODEL_PATH} \
    --alias ${HEALTH_COACH_LLM_MODEL} \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -t 4

Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Verantwortung:

- lokales GGUF-Modell laden,
- OpenAI-kompatible HTTP-Schnittstelle bereitstellen,
- nur auf Loopback lauschen,
- sich bei einem Prozessfehler selbst neu starten.

### 7.3 `health-coach-api.service`

Datei:

```text
/etc/systemd/system/health-coach-api.service
```

```ini
[Unit]
Description=Health Coach API
After=health-coach-prepare.service health-coach-llm.service
Requires=health-coach-prepare.service
Wants=health-coach-llm.service

[Service]
Type=simple
User=coach
Group=coach

WorkingDirectory=/opt/health-coach/backend

Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/etc/health-coach/backend.env

ExecStart=/opt/health-coach/backend/.venv/bin/python \
    -m uvicorn apps.api.main:app \
    --host 127.0.0.1 \
    --port 8000

Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Verantwortung:

- FastAPI-Anwendung bereitstellen,
- Workout-, Profil-, Check-in-, Coaching- und Speech-Funktionen bereitstellen,
- bei aktiviertem LLM dessen lokale OpenAI-kompatible Schnittstelle verwenden,
- bei LLM-Fehlern nicht selbst beendet werden.

### 7.4 `health-coach-device-agent.service`

Datei:

```text
/etc/systemd/system/health-coach-device-agent.service
```

```ini
[Unit]
Description=Health Coach Device Agent
After=bluetooth.service health-coach-api.service
Wants=bluetooth.service
Requires=health-coach-api.service

[Service]
Type=simple
User=coach
Group=coach

WorkingDirectory=/opt/health-coach/backend

Environment=PYTHONUNBUFFERED=1

ExecStart=/opt/health-coach/backend/.venv/bin/python \
    -m apps.device_agent.main

Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Verantwortung:

- Bluetooth-/Geräte-Lebenszyklus verwalten,
- FTMS- und Heart-Rate-Geräte anbinden,
- Telemetrie in die Anwendung einspeisen.

Die API ist eine harte Voraussetzung für den Device Agent.

### 7.5 Caddy und Chromium-Kiosk

Caddy ist der Produktions-Webserver für das gebaute React-Frontend und Reverse Proxy für FastAPI. Es existiert daher kein separater Health-Coach-Frontend-Service.

Produktionsfluss:

```text
Chromium-Kiosk
    -> Caddy :80
       ├─ /api/*    -> FastAPI 127.0.0.1:8000
       ├─ /ws/*     -> FastAPI 127.0.0.1:8000
       ├─ /videos/* -> FastAPI 127.0.0.1:8000
       └─ /*        -> /opt/health-coach/frontend/dist
```

Chromium wird aus der grafischen Benutzersitzung über `deploy/start-kiosk.sh` gestartet. Der Launcher soll auf eine erfolgreiche HTTP-Antwort von Caddy warten, damit kein Fehler-/Leerbildschirm vor dem Webserver erscheint.

---

## 8. Environment-Konfiguration

### 8.1 Verzeichnis anlegen

Einmalig:

```bash
sudo mkdir -p /etc/health-coach
sudo chown root:root /etc/health-coach
sudo chmod 755 /etc/health-coach
```

### 8.2 Backend-Konfiguration

Datei:

```text
/etc/health-coach/backend.env
```

```ini
HEALTH_COACH_LLM_ENABLED=1
HEALTH_COACH_LLM_BASE_URL=http://127.0.0.1:8080
HEALTH_COACH_LLM_MODEL=health-coach-local
HEALTH_COACH_LLM_TIMEOUT_SECONDS=15

# Piper Coach-Stimme
HEALTH_COACH_PIPER_MODEL=/opt/health-coach/data/models/piper-tts/de_DE-thorsten-medium.onnx
HEALTH_COACH_TTS_LENGTH_SCALE=0.92
HEALTH_COACH_TTS_NOISE_SCALE=0.70
HEALTH_COACH_TTS_NOISE_W_SCALE=0.85
HEALTH_COACH_TTS_VOLUME=1.0

# Trainingsvideos
HEALTH_COACH_VIDEO_DIR=/opt/health-coach/data/videos
HEALTH_COACH_VIDEO_SCAN_INTERVAL_SECONDS=300
```

| Variable | Bedeutung |
|---|---|
| `HEALTH_COACH_LLM_ENABLED` | Schaltet die lokale LLM-Integration im Backend ein |
| `HEALTH_COACH_LLM_BASE_URL` | Basis-URL des lokalen `llama-server` |
| `HEALTH_COACH_LLM_MODEL` | Gemeinsamer Modellalias von API und `llama-server` |
| `HEALTH_COACH_LLM_TIMEOUT_SECONDS` | Maximale Wartezeit des Backends auf eine LLM-Antwort |
| `HEALTH_COACH_PIPER_MODEL` | Pfad zum lokalen Piper-ONNX-Modell |
| `HEALTH_COACH_TTS_LENGTH_SCALE` | Sprechtempo von Piper; kleiner als `1.0` spricht schneller |
| `HEALTH_COACH_TTS_NOISE_SCALE` | Variation in der Audioerzeugung |
| `HEALTH_COACH_TTS_NOISE_W_SCALE` | Variation der Phonemdauern / des Sprechrhythmus |
| `HEALTH_COACH_TTS_VOLUME` | Lautstaerke-Multiplikator der Synthese |
| `HEALTH_COACH_VIDEO_DIR` | Physisches Root-Verzeichnis der Trainingsvideos; DB-Pfade sind relativ dazu |
| `HEALTH_COACH_VIDEO_SCAN_INTERVAL_SECONDS` | Intervall der periodischen Katalog-Synchronisation; `0` deaktiviert den periodischen Scan |

Die angegebenen TTS-Werte bilden das aktuelle Coach-Preset. Sie koennen auf dem Produktivsystem ohne Codeaenderung angepasst werden; danach reicht ein Neustart der API. Sehr hohe Noise-Werte koennen die Verstaendlichkeit verschlechtern.

`deploy/provision.sh` lädt die konfigurierte Piper-Stimme vor einem Neustart zur Prüfung mit derselben Bibliothek wie die API. Bei einem defekten Modell werden neue Modell- und Konfigurationsdatei zunächst separat heruntergeladen und geprüft. Erst danach werden die Dateien ersetzt; die alten Dateien bleiben als `.bak.<kennung>` im Modellverzeichnis erhalten. Schlägt Download oder Prüfung fehl, bricht die Bereitstellung ab und lässt die vorhandenen Dateien unverändert. Für diese Prüfung braucht die Bereitstellung Netzwerkzugang; der normale API-Start lädt keine Modelle herunter.

### Wenn die Coach-Ansagen ausbleiben

Während eines Workouts zeigt „Coach online“ nur die WebSocket-Verbindung an. Eine Ansage entsteht beim Verbinden, bei Phasenwechseln und bei relevanten, ausreichend lang anhaltenden Pulsabweichungen. Der Trainingsabschluss-Sound benutzt eine eigene Audiodatei und bestätigt daher nicht die Funktion der Piper-Stimme.

1. „Testansage“ im Workout anklicken. Der angezeigte Sprachstatus unterscheidet Synthese, Wiedergabe, Browser-Fallback und Fehlschlag; ein sichtbarer Hinweis erscheint bei Fallback oder Ausfall. Die Testansage funktioniert auch ohne Pulssensor und ohne Live-Coaching-Event.
2. Bleibt „Coach verbindet …“ stehen, im Chromium-Entwicklerwerkzeug unter Network die Verbindung `/ws/coaching` prüfen. Bei Verbindung ohne Live-Hinweise den Pulssensor, die `/ws/device-agent`-Verbindung und die aktuelle Workout-Phase prüfen. Nach dem Start wird eine erste Ansage beim Verbindungsaufbau ausgelöst.
3. Steht „Browserstimme versucht“ oder „Ansage fehlgeschlagen“, auf dem Coach-PC die lokale Synthese testen:

   ```bash
   curl -sS -o /tmp/coach-test.wav -w 'HTTP %{http_code}, Typ %{content_type}, Bytes %{size_download}\n' \
     -H 'Content-Type: application/json' \
     -d '{"text":"Dies ist eine Testansage."}' \
     http://127.0.0.1/api/speech/synthesize
   journalctl -u health-coach-api -n 100 --no-pager
   ```

   HTTP 200 mit einer WAV-Datei deutet auf ein Wiedergabeproblem im Browser. Bei 503 den konfigurierten `HEALTH_COACH_PIPER_MODEL`-Pfad, die zugehörige `.onnx.json`-Datei, Dateirechte und die installierten Backend-Abhängigkeiten prüfen. Bei 500 den Python-Traceback im API-Journal prüfen. Auch in der Chromium-Konsole stehen Fehler zur lokalen Audiowiedergabe und zum Browser-Fallback.

Falls das LLM vorübergehend deaktiviert werden soll:

```ini
HEALTH_COACH_LLM_ENABLED=0
```

### 8.3 LLM-Konfiguration

Datei:

```text
/etc/health-coach/llm.env
```

```ini
HEALTH_COACH_LLM_MODEL_PATH=/opt/health-coach/data/models/llm/qwen3.5-0.8b-q4_0.gguf
HEALTH_COACH_LLM_MODEL=health-coach-local
```

| Variable | Bedeutung |
|---|---|
| `HEALTH_COACH_LLM_MODEL_PATH` | Pfad zur lokalen GGUF-Datei |
| `HEALTH_COACH_LLM_MODEL` | Alias, unter dem das Modell angeboten wird |

### 8.4 Rechte

Aktuell enthalten diese Dateien keine Secrets.

```bash
sudo chown root:root /etc/health-coach/*.env
sudo chmod 644 /etc/health-coach/*.env
```

Falls später Secrets aufgenommen werden, müssen die Berechtigungen entsprechend restriktiver werden.

### 8.5 Automatischer Konfigurationsabgleich

Die Dateien unter `deploy/etc/health-coach/` sind die Soll-Vorlagen für die beiden Environment-Dateien. `provision.sh` vergleicht dabei **Schlüsselnamen**, nicht die lokalen Werte:

- fehlende Schlüssel können mit dem Vorlagenwert ergänzt werden,
- nicht mehr in der Vorlage vorhandene Schlüssel können entfernt werden,
- vorhandene lokale Werte werden nicht automatisch überschrieben.

Die systemd-Units werden als komplette Dateien gegen `deploy/etc/systemd/system/` verglichen. `backend/alembic.ini` wird bewusst **nicht** automatisch mit Dateien unter `/etc` synchronisiert; es ist Teil der Anwendung und keine maschinenspezifische Runtime-Konfiguration.

### 8.6 Caddy

Die kanonische Appliance-Konfiguration liegt unter:

```text
deploy/etc/caddy/Caddyfile
```

Neben API und WebSockets wird auch `/videos/*` an FastAPI weitergeleitet. Dadurch kann das Backend das über `HEALTH_COACH_VIDEO_DIR` konfigurierte Verzeichnis unabhängig von seinem physischen Speicherort unter der stabilen Browser-URL `/videos/...` ausliefern.

Bei einer Abweichung von `/etc/caddy/Caddyfile` zeigt `provision.sh` einen Diff und fragt vor dem Ersetzen nach. Anschließend wird immer validiert:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

Nur bei erfolgreicher Validierung folgt:

```bash
sudo systemctl restart caddy.service
```

Schlägt die Validierung nach einer Aktualisierung fehl, wird die vorherige Caddy-Konfiguration aus dem Backup wiederhergestellt und Caddy nicht neu gestartet.

---

## 9. LLM-Runtime

### 9.1 `llama-server`

Erwarteter Installationsort:

```text
/usr/local/bin/llama-server
```

Prüfung:

```bash
/usr/local/bin/llama-server --version
```

`llama-server` wird nicht bei jedem normalen Health-Coach-Update neu gebaut. Die Installation bzw. Aktualisierung der nativen llama.cpp-Runtime ist ein separater administrativer Schritt.

### 9.2 Modell

Erwarteter Modellpfad:

```text
/opt/health-coach/data/models/llm/qwen3.5-0.8b-q4_0.gguf
```

Prüfung:

```bash
ls -lh /opt/health-coach/data/models/llm/qwen3.5-0.8b-q4_0.gguf
```

Das Modell wird durch `provision.sh` bzw. das dort aufgerufene Modell-Provisionierungsskript sichergestellt. Es wird **nicht** bei einem normalen Boot heruntergeladen.

### 9.3 Erreichbarkeit prüfen

```bash
curl http://127.0.0.1:8080/v1/models
```

Logs:

```bash
journalctl -u health-coach-llm.service -f
```

Status:

```bash
systemctl status health-coach-llm.service
```

---

## 10. Update-Prozess

### 10.1 Bevorzugter Aufruf

```bash
cd /opt/health-coach
./deploy/provision.sh
```

Damit wird der bisherige manuelle Ablauf aus `git pull` plus Reboot durch einen kontrollierten Deployment-Ablauf ersetzt.

### 10.2 Empfohlene Reihenfolge in `provision.sh`

```text
1.  git fetch --prune origin / optional Branch prüfen+wechseln / git pull --ff-only / cleanup-branches.sh
2.  Branch und Commit ausgeben
3.  venv sicherstellen
4.  pip aktualisieren
5.  Backend installieren/aktualisieren
6.  TTS-Stimme sicherstellen
7.  LLM-Modell sicherstellen
8.  npm ci
9.  Frontend bauen
10. prepare.sh aufrufen
11. systemctl daemon-reload
12. LLM neu starten
13. API neu starten
14. Device Agent neu starten
15. Caddy validieren und neu starten
16. Status ausgeben
```

Git-Ablauf:

```text
git fetch --prune origin
    -> optional: existiert origin/<branch>?
    -> optional: git switch <branch> (ggf. Tracking-Branch anlegen)
    -> git pull --ff-only
    -> cleanup-branches.sh
    -> Branch + Commit ausgeben
```

Ohne Branchparameter bleibt der aktuelle Branch aktiv. Ein Zielbranch, der nicht auf `origin` existiert, führt vor dem Switch zum Abbruch.

### 10.3 Migration und Boot-Vorbereitung

Die Migration muss sowohl im kontrollierten Update-Pfad als auch beim Boot einer bereits installierten Revision sicher ausführbar sein. Das aktuelle `provision.sh` führt `alembic upgrade head` im Update-Ablauf explizit aus; `prepare.sh` führt dieselbe idempotente Migration beim Boot aus. Ist das Schema bereits aktuell, nimmt Alembic keine weitere Schemaänderung vor.

### 10.4 Service-Restart am Ende

```bash
echo "Reloading systemd configuration ..."
sudo systemctl daemon-reload

echo "Restarting Health Coach services ..."
sudo systemctl restart health-coach-llm.service
sudo systemctl restart health-coach-api.service
sudo systemctl restart health-coach-device-agent.service
```

Das statische Frontend benötigt keinen eigenen Service-Restart; Caddy liest die Dateien aus `frontend/dist`. Caddy wird nach erfolgreicher Konfigurationsvalidierung durch `provision.sh` neu gestartet.

---

## 11. Verantwortungsgrenzen

### `provision.sh`

```text
Source Code
Dependencies
Build-Artefakte
TTS-/LLM-Modelle
Deployment
Service-Restart
```

### `prepare.sh`

```text
lokale Runtime-Voraussetzungen
Datenbankschema
Boot-Vorbereitung
```

### `health-coach-prepare.service`

```text
prepare.sh bei Systemstart ausführen
```

### `health-coach-llm.service`

```text
GGUF-Modell laden
lokalen LLM-HTTP-Service bereitstellen
```

### `health-coach-api.service`

```text
FastAPI / fachliche Anwendung
optionale Nutzung des LLM
deterministischer Fallback bei LLM-Ausfall
```

### `health-coach-device-agent.service`

```text
Bluetooth
FTMS
Heart Rate
Geräte-Lebenszyklus
```

### Caddy / Kiosk

```text
Caddy: frontend/dist + Reverse Proxy bereitstellen
Chromium: Anwendung in der grafischen Kiosk-Sitzung öffnen
```

---

## 12. systemd aktivieren

Nach dem erstmaligen Anlegen oder Ändern der Unit-Dateien:

```bash
sudo systemctl daemon-reload
```

Services aktivieren:

```bash
sudo systemctl enable health-coach-prepare.service
sudo systemctl enable health-coach-llm.service
sudo systemctl enable health-coach-api.service
sudo systemctl enable health-coach-device-agent.service
```

Caddy muss separat als Systemdienst aktiviert sein; Chromium-Autostart gehört zur grafischen Kiosk-Sitzung.

Direkter Start:

```bash
sudo systemctl start health-coach-prepare.service
sudo systemctl start health-coach-llm.service
sudo systemctl start health-coach-api.service
sudo systemctl start health-coach-device-agent.service
```

---

## 13. Betriebsprüfung

### Status

```bash
systemctl status health-coach-prepare.service
systemctl status health-coach-llm.service
systemctl status health-coach-api.service
systemctl status health-coach-device-agent.service
```

### Logs

```bash
journalctl -u health-coach-prepare.service
journalctl -u health-coach-llm.service
journalctl -u health-coach-api.service
journalctl -u health-coach-device-agent.service
```

Live-Logs:

```bash
journalctl -u health-coach-api.service -f
```

oder:

```bash
journalctl -u health-coach-llm.service -f
```

---

## 14. Fehlerverhalten

### Provisionierung schlägt fehl

Beispiel:

```text
git fetch / switch / pull
    OK
npm ci
    FEHLER
```

Dann muss `provision.sh` wegen `set -euo pipefail` abbrechen. Die Services sollen nicht automatisch auf Basis eines unvollständig provisionierten Stands neu gestartet werden.

### Prepare schlägt fehl

Beispiel:

```text
Alembic-Migration
    FEHLER
```

Dann schlägt `health-coach-prepare.service` fehl. Da API und LLM `Requires=health-coach-prepare.service` verwenden, sollen sie nicht gegen einen nicht vorbereiteten Runtime-Stand starten.

### LLM schlägt fehl

```text
health-coach-llm.service
    FEHLER
```

Die API soll trotzdem laufen.

Begründung:

```text
LLM = optionale Formulierungs-/Assistenzfunktion
API = Kernfunktion
```

### Device Agent schlägt fehl

Die API bleibt aktiv. Sensorik ist eine ergänzende Laufzeitfunktion und darf die Anwendung als Ganzes nicht unbenutzbar machen.

---

## 15. Sicherheit und Netzwerk

LLM:

```text
127.0.0.1:8080
```

API:

```text
127.0.0.1:8000
```

Beide Services lauschen nur auf dem lokalen Loopback-Interface.

Das lokale LLM soll nicht direkt durch das Frontend oder andere Rechner im LAN angesprochen werden.

```text
Frontend
   |
   v
API
   |
   v
Local LLM
```

Die API bleibt damit Integrations- und Kontrollgrenze.

---

## 16. Einmalige Einrichtung

### 16.1 systemd-Dateien installieren

Wenn die Referenzdateien im Repository unter `deploy/systemd/` liegen:

```bash
sudo cp deploy/systemd/health-coach-prepare.service /etc/systemd/system/
sudo cp deploy/systemd/health-coach-llm.service /etc/systemd/system/
sudo cp deploy/systemd/health-coach-api.service /etc/systemd/system/
sudo cp deploy/systemd/health-coach-device-agent.service /etc/systemd/system/
```

Danach:

```bash
sudo systemctl daemon-reload
```

### 16.2 Environment-Dateien installieren

```bash
sudo mkdir -p /etc/health-coach
```

Anschließend anlegen:

```text
/etc/health-coach/backend.env
/etc/health-coach/llm.env
```

### 16.3 llama.cpp installieren

`llama-server` muss hier verfügbar sein:

```text
/usr/local/bin/llama-server
```

Prüfung:

```bash
/usr/local/bin/llama-server --version
```

### 16.4 Anwendung provisionieren

```bash
cd /opt/health-coach
./deploy/provision.sh
```

### 16.5 Services aktivieren

```bash
sudo systemctl enable health-coach-prepare.service
sudo systemctl enable health-coach-llm.service
sudo systemctl enable health-coach-api.service
sudo systemctl enable health-coach-device-agent.service
```

---

## 17. Normalbetrieb

### Update

```bash
cd /opt/health-coach
./deploy/provision.sh
```

### Neustart des Geräts

```bash
sudo reboot
```

Es ist kein `git pull` beim Boot erforderlich.

### Nur API neu starten

```bash
sudo systemctl restart health-coach-api.service
```

### Nur LLM neu starten

```bash
sudo systemctl restart health-coach-llm.service
```

### Device Agent neu starten

```bash
sudo systemctl restart health-coach-device-agent.service
```

---

## 18. Relevante Repository-Struktur

```text
deploy/
├── provision.sh
├── prepare.sh
├── start-kiosk.sh
└── etc/
    ├── caddy/
    │   └── Caddyfile
    ├── health-coach/
    │   ├── backend.env
    │   └── llm.env
    └── systemd/system/
        ├── health-coach-prepare.service
        ├── health-coach-llm.service
        ├── health-coach-api.service
        └── health-coach-device-agent.service
```

Die Dateien unter `deploy/etc/` sind Referenz-/Sollkonfigurationen. `provision.sh` vergleicht sie mit den installierten Dateien unter `/etc`, zeigt Abweichungen und fragt vor Änderungen nach (oder bestätigt sie mit `--yes`).

---

## 19. Kiosk-Betrieb

Der Kiosk-Benutzer wird in die grafische Sitzung angemeldet; Chromium wird aus dem Desktop-Autostart über `/opt/health-coach/deploy/start-kiosk.sh` gestartet. Der Browser gehört bewusst nicht in einen systemweiten Service, weil er die grafische Benutzer-Session benötigt.

Manueller Test:

```bash
/opt/health-coach/deploy/start-kiosk.sh
```

Wenn der Launcher auf `Waiting for Health Coach ...` stehen bleibt, zuerst Caddy prüfen:

```bash
curl -I http://127.0.0.1/
```

---

## 20. Troubleshooting

### Node/npm im Provisioning nicht verfügbar oder zu alt

Das Provisioning erwartet eine systemweit erreichbare Node.js-24-LTS-Installation (mindestens 24.15.0). Ein nur über interaktives `nvm` aktiviertes Node steht systemd/Skripten nicht zuverlässig zur Verfügung. Prüfen:

```bash
node --version
npm --version
which node
which npm
```

### Frontend erhält HTML statt JSON (`Unexpected token '<'`)

Direkt gegen FastAPI und danach über Caddy prüfen:

```bash
curl -i http://127.0.0.1:8000/api/persons
curl -i http://127.0.0.1/api/persons
```

Wenn nur die Caddy-Anfrage HTML liefert, muss `/api/*` vor dem SPA-Fallback an FastAPI weitergeleitet werden. Entsprechendes gilt für `/videos/*`: ein Video-Request darf nicht in `index.html` fallen.

### Trainingsvideo wird nicht abgespielt

Zuerst den in der DB/API gespeicherten `filePath` prüfen. Er muss relativ zum Video-Root sein, z. B. `cycling/alpen.mp4`. Danach beide Pfade testen:

```bash
curl -I http://127.0.0.1:8000/videos/cycling/alpen.mp4
curl -I http://127.0.0.1/videos/cycling/alpen.mp4
```

Beide Antworten sollen einen Video-Content-Type liefern. Liefert Port 80 HTML, fehlt `/videos/*` im Caddy-Reverse-Proxy.

### Caddy-Konfiguration prüfen

```bash
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl status caddy
journalctl -u caddy -n 100
```

### Caddy zeigt die Default-Seite oder falsche Inhalte

Aktive Konfiguration und Build prüfen:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
ls -lh /opt/health-coach/frontend/dist/index.html
curl -I http://127.0.0.1/
```

Die Repo-Vorlage liegt unter `deploy/etc/caddy/Caddyfile`; `provision.sh` kann Abweichungen anzeigen und nach Bestätigung aktualisieren.

### Port bereits belegt

Produktion verwendet FastAPI auf `127.0.0.1:8000`, Caddy auf Port 80 und das lokale LLM auf `127.0.0.1:8080`. Prüfen:

```bash
ss -ltnp | grep -E ':(80|8000|8080)\b'
```

Entwicklungsports richten sich nach der aktuellen Makefile-/Vite-Konfiguration.

### SQLite kann Datei nicht öffnen

```bash
ls -ld /opt/health-coach/data /opt/health-coach/data/db
ls -l /opt/health-coach/data/db/health-coach.db
```

Verzeichnis und Datei müssen für den Service-Benutzer `coach` zugreifbar sein.

### SQLite meldet fehlende Tabellen

```bash
cd /opt/health-coach/backend
.venv/bin/python -m alembic upgrade head
```

### Bluetooth `org.bluez.Error.InProgress` / keine Telemetrie

Sicherstellen, dass nur ein Device Agent auf die Hardware zugreift:

```bash
ps aux | grep -E "device_agent|python.*health-coach|python.*Coach" | grep -v grep
bluetoothctl show
```

Falls BlueZ hängt:

```bash
sudo systemctl restart bluetooth
sudo systemctl restart health-coach-device-agent.service
```

Erwartete Telemetrie-Kette:

```text
BLE device -> Device Agent -> /ws/device-agent -> FastAPI -> /ws/telemetry -> frontend
```
