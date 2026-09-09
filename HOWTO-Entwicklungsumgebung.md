# Howto: Entwicklungsumgebung einrichten

Diese Anleitung beschreibt die lokale Entwicklungsumgebung für das Health-Coach-Projekt unter Windows 11, Linux und macOS. Eine WSL-Installation ist für die normale Entwicklung unter Windows nicht erforderlich.

## 1. Voraussetzungen

| Werkzeug | Zweck | Hinweise |
| --- | --- | --- |
| Git | Repository klonen und Versionsverwaltung | Git Bash ist unter Windows optional. |
| Python | Backend, Tests und Entwicklungswerkzeuge | Die verwendete Projektversion muss unterstützt werden. Python 3.14.7 wurde unter Windows bereits verwendet; die tatsächliche Kompatibilität der Projektabhängigkeiten ist maßgeblich. |
| pip | Python-Paketverwaltung | Wird über den Python-Interpreter aufgerufen. |
| venv | Isolierte Python-Umgebung | Bestandteil der Python-Standardbibliothek. |
| Node.js | JavaScript-Laufzeit für das Frontend | Eine vom Frontend unterstützte Version verwenden; gegebenenfalls `.nvmrc`, `package.json` oder die Projekt-Dokumentation beachten. |
| npm | Frontend-Abhängigkeiten und Skripte | Wird üblicherweise mit Node.js installiert. |
| GNU Make | Ausführen der Projekt-Targets | Unter Windows separat installieren. |
| Datenbank | Backend und Alembic-Migrationen | Datenbanktyp, Version, Zugangsdaten und Startverfahren gemäß Projektkonfiguration bereitstellen. |

Zusätzliche Dienste, Umgebungsvariablen und Zugangsdaten hängen von der Projektkonfiguration ab. Diese Anleitung setzt keine nicht dokumentierten Datenbank- oder Docker-Anforderungen voraus.

### Windows 11

Python kann über den offiziellen Installer von python.org installiert werden. Den Python Launcher `py` und gegebenenfalls die PATH-Integration mitinstallieren. Node.js über den offiziellen Installer von nodejs.org installieren. Git for Windows stellt Git und Git Bash bereit.

GNU Make ist nicht Bestandteil von Windows. Eine Möglichkeit ist GnuWin32 Make, beispielsweise über winget, sofern das Paket im eigenen Katalog verfügbar ist:

```powershell
winget install --id GnuWin32.Make -e
```

Falls Make danach nicht im PATH liegt, kann es direkt aufgerufen werden:

```powershell
& "C:\Program Files (x86)\GnuWin32\bin\make.exe" --version
```

Der Installationspfad kann abweichen. Alternativ eignet sich MSYS2 mit `pacman -S make`. Bei MSYS2 ist zu beachten, dass dessen Shell und Toolchain nicht identisch mit PowerShell oder GnuWin32 sind. Für dieses Projekt wird PowerShell mit einem Windows-kompatiblen Makefile empfohlen.

### Linux

Python, pip, venv, Git, Node.js/npm und Make über den Paketmanager beziehungsweise eine geeignete Node-Versionsverwaltung installieren. Auf Debian/Ubuntu werden beispielsweise die Pakete `python3-venv`, `python3-pip`, `git` und `make` benötigt. Die konkreten Paketnamen und Python-Versionen hängen von der Distribution ab.

### macOS

Python, Git, Node.js und Make installieren, beispielsweise über Homebrew oder die jeweiligen offiziellen Installer. Die Xcode Command Line Tools stellen unter anderem Make bereit. Bei mehreren Python-Versionen den gewünschten Interpreter ausdrücklich auswählen.

## 2. Installation prüfen

### Windows PowerShell

```powershell
py --version
py -m pip --version
node --version
npm --version
git --version
make --version
```

Wenn `make` nicht im PATH liegt, den vollständigen Pfad zur ausführbaren Datei verwenden. Ein neues Terminal öffnen, nachdem Installationsprogramme den PATH geändert haben.

### Linux/macOS

```bash
python3 --version
python3 -m pip --version
node --version
npm --version
git --version
make --version
```

Die Versionsnummern von Node.js und Python müssen zu den Anforderungen des Projekts passen. Eine beliebige neueste Version ist nicht automatisch mit allen Abhängigkeiten kompatibel.

## 3. Repository und Projektstruktur

Repository klonen und in den Projekt-Root wechseln:

```bash
git clone <REPOSITORY-URL>
cd health-coach
```

Die relevante Struktur ist:

```text
health-coach/
├── Makefile
├── backend/
│   ├── pyproject.toml
│   ├── .venv/              # wird lokal erstellt
│   └── ...
└── frontend/
    ├── package.json
    └── ...
```

Die virtuelle Umgebung liegt im Ordner `backend`, nicht im Repository-Root. Alle Make-Targets werden aus dem Repository-Root ausgeführt.

## 4. Python-Entwicklungsumgebung installieren

Das Projekt verwendet eine editierbare Installation mit dem Extra `dev`. Der bestätigte Installationsbefehl lautet:

```text
python -m pip install -e ".[dev]"
```

Damit werden das Backend und die in `backend/pyproject.toml` definierten Entwicklungsabhängigkeiten installiert. Die tatsächlich erforderlichen Pakete und Versionen werden durch diese Projektdatei festgelegt; sie sollten nicht durch eine separat geratene Paketliste ersetzt werden.

### Windows PowerShell

Vom Repository-Root aus:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Die venv muss für diese Befehle nicht aktiviert werden. Der direkte Aufruf ihres Python-Interpreters stellt sicher, dass pip in die richtige Umgebung installiert.

### Linux/macOS

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
```

Falls `python3` nicht die gewünschte Version ist, den passenden Interpreter verwenden, beispielsweise `python3.12 -m venv .venv`, sofern diese Version vom Projekt unterstützt wird.

### Installation prüfen

Unter Windows:

```powershell
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -m ruff --version
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -m mypy --version
```

Unter Linux/macOS entsprechend `.venv/bin/python` verwenden. Ruff, pytest, mypy, Alembic und Uvicorn werden durch die Projektabhängigkeiten bereitgestellt, sofern sie dort deklariert sind. Fehlende Pakete sollten in `pyproject.toml` ergänzt und anschließend über das `dev`-Extra installiert werden.

## 5. Virtuelle Umgebung optional aktivieren

Die Aktivierung ist für das Makefile und für direkte Interpreteraufrufe nicht erforderlich. Sie ist nur praktisch, wenn man interaktiv `python` und `pip` verwenden möchte.

| Shell | Aktivierung |
| --- | --- |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Git Bash unter Windows | `source .venv/Scripts/activate` |
| Linux/macOS Bash/Zsh | `source .venv/bin/activate` |

Die Befehle werden im Ordner `backend` ausgeführt. Zum Verlassen der aktivierten Umgebung dient `deactivate`.

Falls PowerShell die Aktivierung wegen der Execution Policy blockiert, kann die Policy nur für die aktuelle Sitzung angepasst werden:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Anschließend die Aktivierung erneut ausführen. Eine Fehlermeldung, dass `Activate.ps1` nicht gefunden wurde, ist dagegen ein Pfad- oder Erstellungsproblem und kein Execution-Policy-Problem.

## 6. Frontend installieren

In den Frontend-Ordner wechseln und die Node-Abhängigkeiten installieren:

```bash
cd frontend
npm ci
```

`npm ci` ist für reproduzierbare Installationen mit vorhandener, gültiger `package-lock.json` vorgesehen. Falls das Projekt keine Lockdatei besitzt oder diese nicht zur `package.json` passt, muss die Paketkonfiguration geklärt werden; für die initiale Erstellung einer Lockdatei wird üblicherweise `npm install` verwendet.

Anschließend die verfügbaren Skripte prüfen:

```bash
npm run
```

Das Makefile verwendet unter anderem `dev`, `lint`, `format`, `format:check`, `build` und `test`. Diese Skripte müssen in `frontend/package.json` definiert sein. `npx tsc --noEmit` setzt außerdem die entsprechenden TypeScript-Abhängigkeiten voraus.

## 7. Makefile plattformübergreifend verwenden

Das Makefile wählt den Python-Interpreter anhand des Betriebssystems:

```makefile
ifeq ($(OS),Windows_NT)
PYTHON := .venv\Scripts\python.exe
else
PYTHON := .venv/bin/python
endif
```

Wichtig: `PYTHON` und `SHELL` sind Make-Variablenzuweisungen und dürfen nicht mit einem Tabulator eingerückt werden. Nur die Befehlszeilen unter Targets beginnen mit einem echten Tabulator.

Ein plattformübergreifendes Target ruft den Interpreter direkt auf:

```makefile
format:
	cd backend && $(PYTHON) -m ruff format .
	cd backend && $(PYTHON) -m ruff check . --fix
	cd frontend && npm run format
```

Die Pfade sind relativ zu `backend`, weil vor dem Python-Aufruf `cd backend` ausgeführt wird. Eine Aktivierung mit `source` oder `. .venv/bin/activate` ist nicht nötig.

### Verfügbare Targets

| Target | Funktion |
| --- | --- |
| `make dev` | Backend, Device-Agent und Frontend gemeinsam starten. |
| `make backend` | Alembic-Migrationen ausführen und Uvicorn starten. |
| `make device-agent` | Device-Agent starten. |
| `make frontend` | Frontend-Entwicklungsserver starten. |
| `make test` | Backend-Tests mit pytest ausführen. |
| `make check` | Formatprüfung sowie Backend- und Frontend-Checks ausführen. |
| `make check-backend` | Ruff, mypy und pytest ausführen. |
| `make check-frontend` | Lint, Formatprüfung, TypeScript, Build und Tests ausführen. |
| `make format` | Backend und Frontend formatieren. |
| `make format-check` | Backend-Formatierung prüfen. |
| `make build` | Checks und Frontend-Build ausführen. |
| `make db-upgrade` | Datenbank auf die aktuelle Alembic-Revision bringen. |
| `make db-current` | Aktuelle Datenbankrevision anzeigen. |
| `make db-history` | Migrationshistorie anzeigen. |
| `make migration m="Beschreibung"` | Neue automatisch generierte Migration erstellen. |

Unter Windows ohne Make im PATH beispielsweise:

```powershell
& "C:\Program Files (x86)\GnuWin32\bin\make.exe" format
```

### Besonderheit: `make dev`

Das ursprüngliche `dev`-Target verwendet POSIX-Shell-Funktionen wie `trap`, `kill`, `exec`, `wait` und `$!`. Diese funktionieren nicht unverändert unter Windows-CMD. Deshalb benötigt das gemeinsame Starten und Stoppen der drei Dienste eine plattformabhängige Implementierung oder einen separaten plattformübergreifenden Prozessmanager.

Die bisherigen Python- und Frontend-Targets sind durch direkte Interpreteraufrufe portabel. Das Windows-`dev`-Target mit PowerShell und `Start-Process` sollte jedoch nicht als vollständig verifiziert gelten: Das Beenden des gestarteten Make-Prozesses garantiert nicht, dass alle Kindprozesse, insbesondere Uvicorns Reload-Prozess und Node.js, ebenfalls beendet werden. Für zuverlässiges Ctrl-C- und Prozessgruppenverhalten empfiehlt sich ein gesondert getestetes Startskript oder ein geeigneter Prozessmanager. Bis dahin können die drei Dienste in getrennten Terminals gestartet und jeweils mit Ctrl-C beendet werden.

## 8. Entwicklungsserver starten

Zunächst sicherstellen, dass die erforderliche Datenbank und sonstige projektabhängige Dienste laufen und die benötigten Umgebungsvariablen gesetzt sind. Die konkreten Werte müssen aus der Projektkonfiguration übernommen werden.

Aus dem Repository-Root:

```bash
make backend
```

In einem zweiten Terminal:

```bash
make device-agent
```

In einem dritten Terminal:

```bash
make frontend
```

Das Backend-Target führt vor dem Start `alembic upgrade head` aus und startet Uvicorn auf `0.0.0.0:8000` mit Reload. Das Frontend wird über das in `package.json` definierte npm-Skript gestartet. Der Device-Agent wird als Python-Modul ausgeführt.

`0.0.0.0` bindet einen Dienst an alle verfügbaren Netzwerkschnittstellen. Wer nur lokal entwickeln möchte, sollte prüfen, ob eine Bindung an `127.0.0.1` ausreicht. Firewall- und Netzwerkfreigaben sind entsprechend zu berücksichtigen.

## 9. Typischer Arbeitsablauf

Nach dem ersten Setup:

```bash
# Im Repository-Root
make format
make test
make check
```

Bei Änderungen an Python-Abhängigkeiten:

```powershell
# Windows, im backend-Ordner
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

```bash
# Linux/macOS, im backend-Ordner
.venv/bin/python -m pip install -e ".[dev]"
```

Bei Änderungen an Frontend-Abhängigkeiten:

```bash
cd frontend
npm ci
```

## 10. Häufige Fehler

### `Activate.ps1` wurde nicht gefunden

Die venv existiert nicht am erwarteten Ort oder wurde in einem anderen Ordner erstellt. Im `backend`-Ordner prüfen:

```powershell
Test-Path .\.venv\Scripts\Activate.ps1
```

Falls `False`, die Umgebung mit `py -m venv .venv` erstellen. Nicht vorschnell die Execution Policy ändern.

### `make` wurde nicht gefunden

Make ist nicht installiert oder sein Installationsordner fehlt im PATH. `make --version` prüfen, das Terminal neu öffnen oder die ausführbare Datei über ihren vollständigen Pfad aufrufen.

### `Der Befehl "." ... konnte nicht gefunden werden`

Das Makefile verwendet Unix-Aktivierung unter Windows-CMD. Statt `. .venv/bin/activate` den Python-Interpreter der venv direkt verwenden. Das gilt auch für Alembic: `$(PYTHON) -m alembic`.

### `No module named ruff`

Die Entwicklungsabhängigkeiten fehlen in der verwendeten venv. Im Backend-Ordner:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Unter Linux/macOS `.venv/bin/python` verwenden. Falls das Paket danach weiterhin fehlt, die Definition des `dev`-Extras in `pyproject.toml` prüfen.

### `missing separator`

Makefile-Syntax prüfen. Rezeptzeilen müssen mit einem echten Tabulator beginnen. Variablenzuweisungen und `ifeq`/`else`/`endif` dürfen nicht wie Rezeptzeilen eingerückt sein. Außerdem sicherstellen, dass keine Markdown-Codezäune, typografischen Leerzeichen oder andere Sonderzeichen in die Datei kopiert wurden.

### Falscher Python-Interpreter

Unter Windows:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip --version
```

Unter Linux/macOS die entsprechenden Befehle mit `.venv/bin/python` ausführen. Beide Ausgaben sollten auf die Projekt-venv verweisen.

### Node/npm fehlen oder Frontend-Skripte schlagen fehl

`node --version`, `npm --version` und `npm run` im Frontend prüfen. Die unterstützte Node-Version und die vorhandenen Skripte aus der Projektkonfiguration übernehmen. Anschließend die Frontend-Abhängigkeiten installieren.

## 11. Git und lokale Dateien

Die virtuelle Umgebung und generierte Abhängigkeiten gehören normalerweise nicht ins Repository. Die `.gitignore` sollte mindestens die relevanten lokalen Verzeichnisse ausschließen:

```gitignore
backend/.venv/
frontend/node_modules/
```

Zusätzlich projektspezifische Cache-, Build- und lokale Konfigurationsdateien berücksichtigen. Geheimnisse wie Datenbankpasswörter, API-Keys und lokale `.env`-Dateien dürfen nicht versehentlich eingecheckt werden. Beispielkonfigurationen können ohne echte Zugangsdaten versioniert werden.

## 12. WSL: erforderlich oder optional?

WSL ist für Python, venv, pip, Node.js, npm und Make nicht erforderlich. Natives Windows reicht für die üblichen Entwicklungsaufgaben aus. WSL kann sinnvoll sein, wenn das Projekt Linux-spezifische Werkzeuge, Shell-Skripte oder eine Linux-nahe Container- und Laufzeitumgebung benötigt.

Wer WSL verwendet, sollte Python-venv und Node-Abhängigkeiten innerhalb der Linux-Umgebung neu installieren und nicht die Windows-venv wiederverwenden. Die beiden Umgebungen besitzen unterschiedliche Interpreter und ausführbare Dateien. Für die tägliche Arbeit sollte eine konsistente Toolchain gewählt werden, statt Windows-, Git-Bash- und WSL-Befehle unkontrolliert zu mischen.
