# Übergabe für Wortfrequenz-Analysen

## Ziel

Dieses Paket enthält die lokal gespeicherten boQwI'-Daten für Klingonisch und
alle Dateien, die für spätere Wortlisten- und Worthäufigkeitsanalysen benötigt
werden. Die Daten stammen aus dem öffentlichen Repository
`https://github.com/De7vID/klingon-assistant-data`.

## Was eingelesen wurde

- Upstream-Stand: Branch `main`, Version `2026.07.24b`.
- Der komplette Repository-Snapshot liegt unter `source/`.
- Die aktuelle Datenbankstruktur besteht hauptsächlich aus YAML-Dateien unter
  `source/entries/`; zusätzlich sind die älteren XML-Dateien (`mem-*.xml`),
  Hilfsskripte, README und Lizenz enthalten.
- Die YAML-Struktur ist die maßgebliche Quelle für die aktuelle Wortdatenbank.
  Die XML-Dateien wurden mit heruntergeladen, aber nicht in die CSV gemischt.

## Erzeugte Dateien

- `entries.csv`: flacher Export für Tabellen- und KI-Verarbeitung. Jede Zeile
  entspricht einem YAML-Eintrag und enthält `entry_name`, `category`,
  `source_file` und den vollständigen unveränderten YAML-Text in `yaml`.
- `download_metadata.json`: Quelle, Version und Zählwerte.
- `path_map.json`: Zuordnung, wenn ein Upstream-Dateiname unter Windows nicht
  unverändert gespeichert werden kann.
- `download_dictionary.py`: reproduzierbares Download- und Exportskript; es
  verwendet nur die Python-Standardbibliothek.
- `README.md`: kurze technische Bedienungsanleitung.

## Windows-Dateinamen

Klingonische Groß-/Kleinschreibung ist bedeutungsrelevant. Das Upstream-Repo
enthält daher viele Paare wie `Q`/`q`, die auf Windows kollidieren. Der Import
behält diese Einträge getrennt und versieht den gespeicherten Pfad bei Bedarf
mit `~case2`, `~case3` usw. `path_map.json` dokumentiert die Originalpfade.
Die CSV verwendet weiterhin die originalen Namen und Pfade. Zusätzlich wurde
ein einzelner Upstream-Dateiname mit `?` percent-kodiert, weil Windows dieses
Zeichen in Dateinamen nicht erlaubt.

## Empfehlungen für die nächste KI

1. Für Wortlisten zunächst `entries.csv` verwenden und die YAML-Spalte als
   strukturierten Text analysieren. Die Originaldateien dienen zur Kontrolle.
2. Nicht anhand des Dateinamens deduplizieren: `entry.entry_name` bzw. die
   CSV-Spalte `entry_name` ist die sprachliche Schreibweise.
3. `section` und `status` aus dem YAML berücksichtigen, falls nur kanonische
   Wörter gewünscht sind. `extra` und `examples` sind eigene Bereiche und
   sollten für eine reine Kernwortliste separat behandelt werden.
4. Für Worthäufigkeiten klar trennen zwischen Wörterbuchbestand und einem
   Korpus. Diese Datenbank enthält Bedeutungen, Grammatik, Übersetzungen und
   Beispiele, aber keine reale Nutzungshäufigkeit. Für Frequenzen muss daher
   zusätzlich ein Klingonisch-Korpus analysiert werden.
5. Die YAML-Einträge enthalten mehrsprachige Definitionen; für deutsche
   Analysen sind die deutschen Felder zu bevorzugen, sofern vorhanden, und
   sonst die englischen Felder als Fallback zu verwenden.

## Reproduzierbarkeit

Mit der vorhandenen Python-Installation kann der Export aus diesem Ordner
erneut erstellt werden:

```powershell
& 'C:\Users\chris\AppData\Local\Python\bin\python.exe' .\download_dictionary.py
```

Die Datei `LICENSE` unter `source/` muss bei Weitergabe der Upstream-Daten
erhalten bleiben. Die Rohdaten stehen unter der dort dokumentierten Lizenz.
