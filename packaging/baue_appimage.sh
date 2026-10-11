#!/usr/bin/env bash
# Baut eine neue AppImage aus einer vorhandenen: Laufzeit behalten, Programmdateien ersetzen.
set -euo pipefail
quelle="${1:?Aufruf: packaging/baue_appimage.sh pfad/zur/vorhandenen.AppImage}"
projekt="$(cd "$(dirname "$0")/.." && pwd)"
arbeit="$(mktemp -d)"; trap 'rm -rf "$arbeit"' EXIT
quelle="$(readlink -f "$quelle")"
versatz="$("$quelle" --appimage-offset)"
head -c "$versatz" "$quelle" > "$arbeit/runtime"
(cd "$arbeit" && unsquashfs -q -o "$versatz" -d AppDir "$quelle")
app="$arbeit/AppDir/usr/share/aufmasswerk"
rm -rf "$app"; mkdir -p "$app"
cp "$projekt/src/main.py" "$app/"; cp -r "$projekt/src/themes" "$app/"
cp "$projekt/docs/Bedienungsanleitung.pdf" "$app/"
cp "$projekt/packaging/AppRun" "$arbeit/AppDir/AppRun"; chmod +x "$arbeit/AppDir/AppRun"
cp "$projekt/packaging/aufmasswerk.desktop" "$arbeit/AppDir/aufmasswerk.desktop"
cp "$projekt/packaging/aufmasswerk-256.png" "$arbeit/AppDir/usr/share/icons/hicolor/256x256/apps/aufmasswerk.png"
find "$arbeit/AppDir" -name __pycache__ -prune -exec rm -rf {} +
mksquashfs "$arbeit/AppDir" "$arbeit/app.sqfs" -comp zstd -b 131072 -root-owned -noappend -quiet
cat "$arbeit/runtime" "$arbeit/app.sqfs" > "$projekt/aufmasswerk-neu-x86_64.AppImage"
chmod +x "$projekt/aufmasswerk-neu-x86_64.AppImage"
echo "fertig: $projekt/aufmasswerk-neu-x86_64.AppImage"
