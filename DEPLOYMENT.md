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
├── health-coach-llm.service
└── <Frontend-Service>
```

Der Frontend-Service existiert bereits separat. Seine konkrete Unit ist in diesem Dokument erst vollständig dokumentierbar, sobald deren aktueller `ExecStart` bzw. die Art der Auslieferung bekannt ist.

---

## 3. Komponenten und Verantwortlichkeiten

### 3.1 `provision.sh`

`deploy/provision.sh` ist das **explizite Update- und Deployment-Skript**.

Es wird nicht bei jedem normalen Boot ausgeführt.

Verantwortlichkeiten:

1. Repository aktualisieren (`git pull --ff-only`).
2. Aktuellen Branch und Commit ausgeben.
3. Python Virtual Environment anlegen, falls erforderlich.
4. Backend-Abhängigkeiten installieren bzw. aktualisieren.
5. TTS-Modell/-Stimme provisionieren.
6. LLM-Modell provisionieren.
7. Frontend-Abhängigkeiten reproduzierbar mit `npm ci` installieren.
8. Frontend bauen.
9. `prepare.sh` ausführen, damit Runtime-Vorbereitung und Migrationen nur an einer Stelle definiert sind.
10. systemd-Konfiguration neu laden.
11. Health-Coach-Services neu starten.
12. Fehler sichtbar abbrechen, statt eine teilweise installierte Version weiterzustarten.

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

Ein Reboot ist nach einem erfolgreichen Update grundsätzlich nicht erforderlich.

---

### 3.2 `prepare.sh`

`deploy/prepare.sh` ist die **Boot-Vorbereitung**.

Es wird durch `health-coach-prepare.service` bei einem normalen Systemstart ausgeführt und zusätzlich von `provision.sh` nach erfolgreicher Installation aufgerufen.

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
| Aufruf | manuell | automatisch durch systemd; zusätzlich aus `provision.sh` |
| `git pull` | ja | nein |
| Netzwerk erlaubt | ja | nein |
| Python-Dependencies | installieren/aktualisieren | nein |
| `npm ci` | ja | nein |
| Frontend-Build | ja | nein |
| TTS-Modell | provisionieren | nur vorhandenen Stand verwenden |
| LLM-Modell | provisionieren | nur vorhandenen Stand verwenden |
| Alembic-Migration | indirekt über `prepare.sh` | ja |
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
     +--> git pull --ff-only
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

Ein sinnvoller Git-Abschnitt in `provision.sh` ist:

```bash
cd "${ROOT_DIR}"

echo "Updating repository ..."
git pull --ff-only

CURRENT_BRANCH="$(git branch --show-current)"
CURRENT_COMMIT="$(git rev-parse --short HEAD)"

echo "Current branch: ${CURRENT_BRANCH}"
echo "Current commit: ${CURRENT_COMMIT}"
```

`--ff-only` verhindert, dass das Produktivsystem bei divergierenden Git-Ständen automatisch einen Merge erzeugt.

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

Der Frontend-Service wird ebenfalls durch systemd gestartet und verwendet das bereits durch `provision.sh` gebaute Frontend.

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

### 7.5 Frontend-Service

Das Frontend läuft im Produktivsystem bereits als eigener Service.

Die konkrete Unit sollte ebenfalls in das Repository aufgenommen und hier dokumentiert werden.

Da der aktuelle `ExecStart` bzw. die konkrete Auslieferungsart des Frontends noch nicht vorliegt, wird an dieser Stelle bewusst **keine hypothetische systemd-Konfiguration erfunden**.

Sobald die bestehende Frontend-Unit aufgenommen wurde, sollte diese Sektion mindestens dokumentieren:

- Unit-Dateiname,
- `User` / `Group`,
- `WorkingDirectory`,
- `ExecStart`,
- Port bzw. Bind-Adresse,
- Abhängigkeit von `health-coach-prepare.service`,
- Restart-Policy,
- gegebenenfalls Kiosk-/Browser-Abhängigkeiten.

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
HEALTH_COACH_TTS_LENGTH_SCALE=0.92
HEALTH_COACH_TTS_NOISE_SCALE=0.70
HEALTH_COACH_TTS_NOISE_W_SCALE=0.85
HEALTH_COACH_TTS_VOLUME=1.0
```

| Variable | Bedeutung |
|---|---|
| `HEALTH_COACH_LLM_ENABLED` | Schaltet die lokale LLM-Integration im Backend ein |
| `HEALTH_COACH_LLM_BASE_URL` | Basis-URL des lokalen `llama-server` |
| `HEALTH_COACH_LLM_MODEL` | Gemeinsamer Modellalias von API und `llama-server` |
| `HEALTH_COACH_LLM_TIMEOUT_SECONDS` | Maximale Wartezeit des Backends auf eine LLM-Antwort |
| `HEALTH_COACH_PIPER_MODEL` | Pfad zur lokalen Piper-ONNX-Stimme; Standard im Projekt: `data/models/piper-tts/de_DE-thorsten-medium.onnx` |
| `HEALTH_COACH_TTS_LENGTH_SCALE` | Sprechtempo von Piper; kleiner als `1.0` spricht schneller |
| `HEALTH_COACH_TTS_NOISE_SCALE` | Variation in der Audioerzeugung |
| `HEALTH_COACH_TTS_NOISE_W_SCALE` | Variation der Phonemdauern / des Sprechrhythmus |
| `HEALTH_COACH_TTS_VOLUME` | Lautstaerke-Multiplikator der Synthese |

Die angegebenen TTS-Werte bilden das aktuelle Coach-Preset. Sie koennen auf dem Produktivsystem ohne Codeaenderung angepasst werden; danach reicht ein Neustart der API. Sehr hohe Noise-Werte koennen die Verstaendlichkeit verschlechtern.

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
1.  git pull --ff-only
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
15. Frontend-Service ggf. neu starten
16. Status ausgeben
```

Beispiel für den Git-Teil:

```bash
echo "Updating repository ..."
cd "${ROOT_DIR}"
git pull --ff-only

echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git rev-parse --short HEAD)"
```

### 10.3 Runtime-Vorbereitung nicht duplizieren

`provision.sh` sollte nach Installation und Build einfach aufrufen:

```bash
"${ROOT_DIR}/deploy/prepare.sh"
```

und die Alembic-Migration nicht zusätzlich selbst duplizieren.

### 10.4 Service-Restart am Ende

```bash
echo "Reloading systemd configuration ..."
sudo systemctl daemon-reload

echo "Restarting Health Coach services ..."
sudo systemctl restart health-coach-llm.service
sudo systemctl restart health-coach-api.service
sudo systemctl restart health-coach-device-agent.service
```

Der Frontend-Service ist ebenfalls neu zu starten, falls seine Laufzeit dies nach einem neuen Frontend-Build erfordert.

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

### Frontend-Service

```text
Produktiv-Frontend bereitstellen
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

Zusätzlich den bestehenden Frontend-Service aktivieren.

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
git pull
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

## 18. Empfohlene Repository-Struktur

```text
deploy/
├── provision.sh
├── prepare.sh
├── systemd/
│   ├── health-coach-prepare.service
│   ├── health-coach-llm.service
│   ├── health-coach-api.service
│   ├── health-coach-device-agent.service
│   └── <Frontend-Service>
├── env/
│   ├── backend.env.example
│   └── llm.env.example
└── DEPLOYMENT.md
```

Dabei gilt:

- echte Environment-Dateien unter `/etc/health-coach` werden nicht zwingend versioniert,
- `.example`-Dateien dokumentieren alle erforderlichen Variablen,
- systemd-Units im Repository sind die Referenzkonfiguration,
- `/etc/systemd/system` enthält die tatsächlich installierte Kopie.

---

## 19. Offener Punkt: Frontend-Service

Für eine vollständig geschlossene Deployment-Dokumentation sollte noch die aktuell eingesetzte Frontend-systemd-Unit in das Repository aufgenommen werden.

Danach kann dieses Dokument um die exakte Frontend-Konfiguration und deren Restart-Verhalten ergänzt werden.

Bis dahin sind Backend, Device Agent, Prepare und lokales LLM vollständig beschrieben.
