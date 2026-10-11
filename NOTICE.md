# Verwendete Bausteine

Aufmaßwerk selbst steht unter der GPL-3.0 (siehe `LICENSE`). Es verwendet:

| Baustein | Zweck | Lizenz |
|---|---|---|
| [Python](https://www.python.org/) | Programmiersprache und Laufzeit | PSF License |
| [Qt](https://www.qt.io/) und [PySide6](https://doc.qt.io/qtforpython/) | Oberfläche und PDF-Erzeugung | LGPL-3.0 |
| [pypdf](https://github.com/py-pdf/pypdf) | Einbetten und Auslesen der E-Rechnungsdaten | BSD-3-Clause |
| [typing_extensions](https://github.com/python/typing_extensions) | Hilfsbibliothek für pypdf | PSF License |
| SQLite | Datenbank | gemeinfrei |

Die AppImage enthält diese Bausteine in unveränderter Form. Die E-Rechnung folgt der Norm EN 16931 und dem Format Factur-X / ZUGFeRD.
