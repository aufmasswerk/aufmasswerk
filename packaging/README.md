# AppImage bauen

Die AppImage enthält eine Python-Laufzeit (3.10), PySide6 und pypdf. Damit niemand diese Laufzeit von Grund auf neu zusammenstellen muss, wird eine neue AppImage aus einer vorhandenen gebaut: Das Skript packt eine veröffentlichte AppImage aus, ersetzt darin die Programmdateien aus diesem Projekt und packt sie wieder ein.

```bash
packaging/baue_appimage.sh pfad/zur/aufmasswerk-vorherige-x86_64.AppImage
```

Das Ergebnis liegt danach als `aufmasswerk-neu-x86_64.AppImage` im Projektordner. Benötigt wird das Paket `squashfs-tools` (`mksquashfs`, `unsquashfs`).

Dateien in diesem Ordner:

- `AppRun` – Startskript in der AppImage
- `aufmasswerk.desktop` – Eintrag für das Startmenü
- `aufmasswerk.svg`, `aufmasswerk-256.png` – Programmsymbol
