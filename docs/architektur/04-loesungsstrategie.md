# 4. Lösungsstrategie

1. **Package-by-Feature** statt einer globalen Schichtenstruktur.
2. Domänenmodelle bleiben frei von Infrastrukturwissen.
3. `service/` enthält Use Cases und Anwendungslogik.
4. API-Verträge sind von Domänenobjekten getrennt.
5. Persistenz läuft über Repository-Abstraktionen und SQLAlchemy-Adapter.
6. Cross-Feature-Orchestrierung liegt im App-/Composition-Root, nicht in den Features selbst.
7. Sensorik ist optional und darf den Workout-Lebenszyklus nicht blockieren.
8. Coaching-Entscheidungen werden zuerst deterministisch getroffen.
9. Entscheidung, Formulierung, Speech Policy und Audioerzeugung sind getrennte Verantwortlichkeiten.
10. Ein lokales LLM ist optional und erhält nur explizit ausgewählte Coaching-Fakten.
11. Ein LLM-Ausfall führt zum deterministischen Fallback, nicht zum Ausfall der Anwendung.
12. Lokale TTS wird über einen Port gekapselt; Piper ist die aktuelle Implementierung.
13. Deployment und Boot-Vorbereitung sind getrennt: `provision.sh` vs. `prepare.sh`.
14. Änderungen werden in kleinen, testbaren Schritten umgesetzt.

---
