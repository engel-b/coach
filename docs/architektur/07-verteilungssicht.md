# 7. Verteilungssicht

## 7.1 Entwicklung

```text
+---------------------- Entwickler-PC -----------------------+
| React Dev Server                                            |
| FastAPI Backend                                             |
| Device Agent                                                |
| SQLite DB                                                   |
| Piper TTS                                                   |
| llama-server [optional]                                     |
| Bluetooth Hardware [optional]                               |
+-------------------------------------------------------------+
```

## 7.2 Zielbild Appliance

```text
+----------------------- Debian Appliance ----------------------------+
|                                                                      |
|  +------------------+        +--------------------+                   |
|  | Frontend / Kiosk | <----> | FastAPI API        |                   |
|  +------------------+        +----+-----------+---+                   |
|                                  |           |                       |
|                           +------+           +----------------+      |
|                           v                               v           |
|                     +-----+------+                  +-----+------+    |
|                     | SQLite     |                  | Piper TTS  |    |
|                     +------------+                  +------------+    |
|                                  |                                   |
|                         [optional] v                                  |
|                            +-----+------+                             |
|                            | Local LLM  |                             |
|                            | llama-server|                            |
|                            +------------+                             |
|                                                                      |
|  +-------------------+                                               |
|  | Device Agent      | ----> Bluetooth: FTMS / HR                    |
|  +-------------------+                                               |
+----------------------------------------------------------------------+
```

## 7.3 systemd-Abhängigkeiten

```text
Boot
 |
 v
health-coach-prepare.service
 |
 +-----------------------------+
 |                             |
 v                             v
health-coach-llm.service   health-coach-api.service
      [optional]                 |
                                 v
                       health-coach-device-agent.service
```

Die API verwendet für das LLM eine weiche Abhängigkeit (`Wants=` statt `Requires=`). Ein Fehler des LLM-Service darf die API nicht mit herunterziehen.

## 7.4 Provisionierung vs. Boot-Vorbereitung

```text
provision.sh
    = explizites Update / Deployment
    = git fetch --prune + optional Branch-Switch + pull --ff-only
    = cleanup-branches.sh
    = Dependencies
    = Frontend Build
    = TTS-/LLM-Modelle
    = Alembic-Migration
    = Konfigurationsabgleich + Service-Restart

prepare.sh
    = Boot-Vorbereitung
    = offline-fähig
    = keine Downloads
    = keine Builds
    = lokale Runtime-Prüfung
    = Alembic-Migration
```

Die vollständigen Befehle, Environment-Dateien und systemd-Units stehen unter [Deployment und Betrieb](/betrieb/deployment).

---
