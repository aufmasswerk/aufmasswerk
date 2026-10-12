# Aufmaßwerk

**Das Programm fürs Handwerk: Angebot, Aufmaß, Rechnung.**

> **⬇ Programm herunterladen:** [zur aktuellen Version](https://github.com/aufmasswerk/aufmasswerk/releases/latest) – dort die Datei `aufmasswerk-…-x86_64.AppImage` anklicken.
> Bitte nicht den grünen Knopf „Code“ benutzen: Er liefert nur den Quelltext, nicht das fertige Programm.

Aufmaßwerk ist ein Büroprogramm für kleine Handwerksbetriebe, besonders im Ausbau. Es läuft vollständig auf dem eigenen Rechner, ohne Internet, ohne Benutzerkonto und ohne Abo. Entstanden ist es in einem Trockenbaubetrieb aus dem eigenen Bedarf.

![Wirtschaftlicher Stand eines Projekts](docs/bilder/11_wirtschaftlicher_stand.png)

## Was es kann

- **Kunden und Projekte:** alles zu einem Projekt an einem Ort, mit Dokumentenablage.
- **Angebote:** Positionen mit Titeln und Zwischensummen, Formeln für die Mengen, Textblöcke, Leistungsverzeichnisse einlesen (PDF, ODS, Excel), Nachtragsangebote.
- **Aufmaß:** Positionen aus dem Angebot übernehmen und raumweise mit Formeln aufmessen.
- **Rechnungen:** Teil-, Abschlags- und Schlussrechnungen aus dem Aufmaß, kumuliert mit automatischem Abzug früherer Zahlungen, Sicherheitseinbehalt, Skonto, § 13b.
- **E-Rechnung:** Rechnungen werden als ZUGFeRD / Factur-X im Profil EN 16931 ausgegeben (PDF/A-3 mit eingebetteten Rechnungsdaten). Eingehende E-Rechnungen werden ausgelesen.
- **Eingangsrechnungen und wirtschaftlicher Stand:** Kosten je Projekt erfassen und sehen, ob sich das Projekt rechnet.
- **Zahlungen und Mahnungen**, Geschäftsbriefe, eigener Briefbogen als PDF.
- **Datensicherung:** automatische Sicherungen und Komplettsicherung in eine Datei.
- **Leistungssammlung:** jede einmal verwendete Position bleibt für spätere Angebote erhalten.

![Angebot mit Titeln](docs/bilder/05_angebot.png)

## Was es nicht ist

Aufmaßwerk ist **keine Buchhaltung** und ersetzt keinen Steuerberater. Es gibt keine Anbindung an DATEV oder ein Bankkonto.

## Installieren

Aufmaßwerk gibt es für **Linux (x86_64)** als AppImage. Getestet ist es unter Linux Mint 22.

1. Die Datei `aufmasswerk-…-x86_64.AppImage` von der Seite der [aktuellen Version](https://github.com/aufmasswerk/aufmasswerk/releases/latest) herunterladen.
2. Ausführbar machen: Rechtsklick → Eigenschaften → Berechtigungen → „Als Programm ausführbar“.
3. Per Doppelklick starten.

Die Daten liegen getrennt vom Programm im Ordner `~/.local/share/Aufmasswerk`. Ein Update bedeutet: die AppImage-Datei ersetzen.

### Falls es nicht startet

- **Beim Doppelklick passiert nichts (häufig unter Ubuntu):** AppImage-Dateien brauchen die Systembibliothek FUSE 2. Linux Mint bringt sie mit, neuere Ubuntu-Versionen nicht. Nachinstallieren im Terminal:
  - Ubuntu 24.04 und neuer: `sudo apt install libfuse2t64`
  - Ubuntu 22.04: `sudo apt install libfuse2`
- **Ohne Nachinstallieren** startet das Programm auch so aus dem Terminal: `./aufmasswerk-…-x86_64.AppImage --appimage-extract-and-run`
- **Es öffnet sich ein anderes Programm (zum Beispiel Gear Lever):** Manche Systeme fragen zuerst, ob das Programm ins Startmenü aufgenommen werden soll. Nach dem Bestätigen startet Aufmaßwerk über das Startmenü.
- **Die Datei lässt sich nicht ausführen:** Prüfen, ob in den Eigenschaften der Datei das Häkchen „Als Programm ausführbar“ gesetzt ist.

## Anleitung

Die [Bedienungsanleitung](docs/ANLEITUNG.md) führt Schritt für Schritt durch das Programm. Es gibt sie auch als [PDF](docs/Bedienungsanleitung.pdf) und im Programm selbst unter Einstellungen → „Bedienungsanleitung“.

## Hinweise zur E-Rechnung

Die erzeugten Rechnungen wurden mit dem freien Prüfwerkzeug [Mustang](https://www.mustangproject.org/) geprüft: PDF/A-3 und die Regeln der Norm EN 16931 werden eingehalten. Trotzdem gilt: Bitte prüfen Sie Ihre ersten E-Rechnungen selbst und stimmen Sie sich mit Ihrem Steuerberater ab.

Sicherheitseinbehalt und Bauabzug kennt die Norm nicht als eigenes Feld. Aufmaßwerk schreibt sie als Text in die Zahlungsbedingungen; der fällige Betrag in den Rechnungsdaten ist der Betrag vor Einbehalt.

## Haftung

Aufmaßwerk wird so bereitgestellt, wie es ist, **ohne jede Gewähr**. Jeder Anwender ist selbst dafür verantwortlich, dass seine Angebote und Rechnungen inhaltlich und rechtlich richtig sind. Es gibt keinen Anspruch auf Unterstützung.

## Aus dem Quelltext starten

Benötigt werden Python 3.10 oder neuer und die Schrift DejaVu Sans (bei den üblichen Linux-Distributionen vorhanden).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/main.py
```

Mit der Umgebungsvariable `AUFMASSWERK_DATA_DIR` lässt sich ein anderer Datenordner verwenden, zum Beispiel zum Ausprobieren:

```bash
AUFMASSWERK_DATA_DIR=/tmp/aufmasswerk-test .venv/bin/python src/main.py
```

Wie die AppImage gebaut wird, steht in [packaging/README.md](packaging/README.md).

## Zum Quelltext

Das Programm ist in Python mit PySide6 (Qt) geschrieben und steckt in einer einzigen Datei, `src/main.py`. Es ist von einem Handwerker zusammen mit KI-Assistenten entwickelt worden, nicht von einem Softwarehaus. Der Aufbau ist deshalb pragmatisch.

Fehlerberichte und Verbesserungsvorschläge sind willkommen.

## Mitwirkende

Aufmaßwerk ist die Idee eines Handwerkers, der ein Programm für den eigenen Betrieb brauchte. Programmiert haben es zwei KI-Assistenten nach seinen Vorgaben:

- **ChatGPT (OpenAI)** hat mit ihm das Programm von Grund auf entwickelt: Kunden, Projekte, Angebote, Aufmaß, Rechnungen, Zahlungen und Mahnungen.
- **Claude (Anthropic)** hat es später überarbeitet und erweitert: vereinfachte Bedienung, Eingangsrechnungen, E-Rechnung, Datensicherung, Anleitung und Veröffentlichung.

In der automatischen Liste „Contributors“ zeigt GitHub nur Mitwirkende mit einem GitHub-Konto. ChatGPT fehlt dort deshalb, obwohl sein Anteil am Programm groß ist.

## Lizenz

Aufmaßwerk steht unter der [GNU General Public License, Version 3](LICENSE). Jeder darf das Programm nutzen, weitergeben und ändern; geänderte Fassungen müssen unter derselben Lizenz offen bleiben.

Verwendete Bausteine stehen in [NOTICE.md](NOTICE.md).

---

*Aufmaßwerk is a free offline office tool for small German trade businesses: quotes, site measurement, progress and final invoices, ZUGFeRD e-invoices and project cost overview. The user interface and documentation are in German.*
