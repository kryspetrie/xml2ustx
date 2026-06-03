#!/usr/bin/env bash
# Apply xml2ustx integration to keirokeer/OpenUtau-DiffSinger-Lunai (or compatible OpenUtau clone).
# Usage: ./integration/openutau/apply-integration.sh /path/to/OpenUtau-DiffSinger-Lunai
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 /path/to/OpenUtau" >&2
  exit 1
fi

OU_ROOT="$(cd "$1" && pwd)"
INT_ROOT="$(cd "$(dirname "$0")" && pwd)"
XML2USTX_ROOT="$(cd "$INT_ROOT/../.." && pwd)"

echo "Applying integration to $OU_ROOT"

# Copy new source files
cp "$INT_ROOT/OpenUtau.Core/Util/Xml2UstxPaths.cs" "$OU_ROOT/OpenUtau.Core/Util/"
cp "$INT_ROOT/OpenUtau.Core/Util/Xml2UstxInstaller.cs" "$OU_ROOT/OpenUtau.Core/Util/"
cp "$INT_ROOT/OpenUtau.Core/Format/Xml2Ustx.cs" "$OU_ROOT/OpenUtau.Core/Format/"
cp "$INT_ROOT/OpenUtau/ViewModels/Xml2UstxImportViewModel.cs" "$OU_ROOT/OpenUtau/ViewModels/"
cp "$INT_ROOT/OpenUtau/Views/Xml2UstxImportDialog.axaml" "$OU_ROOT/OpenUtau/Views/"
cp "$INT_ROOT/OpenUtau/Views/Xml2UstxImportDialog.axaml.cs" "$OU_ROOT/OpenUtau/Views/"
cp "$INT_ROOT/OpenUtau/Views/Xml2UstxConfigWindow.axaml" "$OU_ROOT/OpenUtau/Views/"
cp "$INT_ROOT/OpenUtau/Views/Xml2UstxConfigWindow.axaml.cs" "$OU_ROOT/OpenUtau/Views/"

mkdir -p "$OU_ROOT/tools/xml2ustx"
cp "$XML2USTX_ROOT/src/resources/config.yml" "$OU_ROOT/tools/xml2ustx/default-config.yml"

export OU_ROOT INT_ROOT
python3 <<'PY'
import os
from pathlib import Path

ou = Path(os.environ["OU_ROOT"])
intf = Path(os.environ["INT_ROOT"])

# Strings.axaml
strings = ou / "OpenUtau/Strings/Strings.axaml"
snippet = (intf / "patches/Strings.axaml.snippet.xml").read_text()
if "menu.file.importmusescore" not in strings.read_text():
    text = strings.read_text()
    anchor = '  <system:String x:Key="menu.file.importtracks">'
    if anchor in text:
        text = text.replace(anchor, snippet.strip() + "\n\n  " + anchor.lstrip())
        strings.write_text(text)
        print("Patched Strings.axaml")

# FilePicker.cs
fp = ou / "OpenUtau/FilePicker.cs"
if "MuseScoreMusicXml" not in fp.read_text():
    fp.write_text(fp.read_text().replace(
        '        public static FilePickerFileType MUSICXML { get; } = new("MUSICXML") {\n'
        '            Patterns = new[] { "*.musicxml" },\n'
        '        };',
        '        public static FilePickerFileType MUSICXML { get; } = new("MUSICXML") {\n'
        '            Patterns = new[] { "*.musicxml" },\n'
        '        };\n'
        '        public static FilePickerFileType MuseScoreMusicXml { get; } = new("MuseScore / MusicXML") {\n'
        '            Patterns = new[] { "*.musicxml", "*.mxl", "*.xml", "*.mid", "*.midi" },\n'
        '        };',
    ))
    print("Patched FilePicker.cs")

# Preferences.cs
prefs = ou / "OpenUtau.Core/Util/Preferences.cs"
if "Xml2UstxTrackConfigId" not in prefs.read_text():
    prefs.write_text(prefs.read_text().replace(
        '            public string WinePath = string.Empty;',
        '            public string WinePath = string.Empty;\n'
        '            public string Xml2UstxTrackConfigId = "default";',
    ))
    print("Patched Preferences.cs")

# MainWindow.axaml
mw = ou / "OpenUtau/Views/MainWindow.axaml"
if "importmusescore" not in mw.read_text():
    mw.write_text(mw.read_text().replace(
        '            <MenuItem Header="{DynamicResource menu.file.importaudio}" Click="OnMenuImportAudio"/>',
        '            <MenuItem Header="{DynamicResource menu.file.importaudio}" Click="OnMenuImportAudio"/>\n'
        '            <MenuItem Header="{DynamicResource menu.file.importmusescore}" Click="OnMenuImportMuseScore"/>',
    ).replace(
        '            <MenuItem Header="{DynamicResource menu.tools.prefs}"',
        '            <MenuItem Header="{DynamicResource menu.tools.xml2ustxdownload}" Click="OnMenuDownloadXml2Ustx"/>\n'
        '            <MenuItem Header="{DynamicResource menu.tools.xml2ustxconfig}" Click="OnMenuEditXml2UstxConfig"/>\n'
        '            <MenuItem Header="{DynamicResource menu.tools.prefs}"',
    ))
    print("Patched MainWindow.axaml")

# MainWindow.axaml.cs
mwc = ou / "OpenUtau/Views/MainWindow.axaml.cs"
if "EnsureXml2UstxSidecarAsync" not in mwc.read_text():
    # Remove legacy handler block if present from an older integration
    import re
    text = mwc.read_text()
    text = re.sub(
        r'\n\s*async void OnMenuImportMuseScore.*?ValidateTracksVoiceColor\(\);\s*\n\s*\}\s*\n',
        '\n',
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'\n\s*void OnMenuEditXml2UstxConfig.*?}\s*\n',
        '\n',
        text,
        count=1,
        flags=re.DOTALL,
    )
    mwc.write_text(text)

if "EnsureXml2UstxSidecarAsync" not in mwc.read_text():
    snippet = (intf / "patches/MainWindow.axaml.cs.snippet.cs").read_text()
    # strip comment header lines
    lines = [l for l in snippet.splitlines() if not l.startswith("//")]
    body = "\n".join(lines).strip()
    text = mwc.read_text()
    insert_at = text.rfind("    }\n}\n")
    if insert_at < 0:
        raise SystemExit("Could not find insertion point in MainWindow.axaml.cs")
    text = text[:insert_at] + body + "\n\n" + text[insert_at:]
    mwc.write_text(text)
    print("Patched MainWindow.axaml.cs")

# OpenUtau.csproj
csproj = ou / "OpenUtau/OpenUtau.csproj"
if "tools\\xml2ustx" not in csproj.read_text() and "tools/xml2ustx" not in csproj.read_text():
    insert = '''  <ItemGroup>
    <None Include="..\\tools\\xml2ustx\\default-config.yml" Link="tools\\xml2ustx\\default-config.yml"
          CopyToOutputDirectory="PreserveNewest" CopyToPublishDirectory="PreserveNewest" />
    <None Include="..\\tools\\xml2ustx\\xml2ustx*" Link="tools\\xml2ustx\\%(Filename)%(Extension)"
          CopyToOutputDirectory="PreserveNewest" CopyToPublishDirectory="PreserveNewest"
          Condition="Exists('..\\tools\\xml2ustx\\xml2ustx') Or Exists('..\\tools\\xml2ustx\\xml2ustx.exe')" />
  </ItemGroup>
'''
    text = csproj.read_text()
    anchor = "  <ItemGroup>\n    <ProjectReference"
    if anchor in text:
        text = text.replace(anchor, insert + "\n" + anchor)
        csproj.write_text(text)
        print("Patched OpenUtau.csproj")
PY

echo "Done. Build sidecar with: $XML2USTX_ROOT/scripts/build_sidecar.sh $OU_ROOT/tools/xml2ustx"
echo "Then: cd $OU_ROOT && dotnet build OpenUtau"
