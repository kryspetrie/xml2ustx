# MusicXML to USTX
Transforms MusicXML (*.mxl, *.xml, *.musicxml, *.midi) into OpenUTAU *.ustx for Singing Voice Synthesis. A rewrite, based on this project: [nicolalandro/xml2ustx](https://github.com/nicolalandro/xml2ustx)
## Usage
```
usage: main.py [-h] [--project_name PROJECT_NAME] [--config_file CONFIG_FILE] [--track_config TRACK_CONFIG] [--voice VOICE] [--pan PAN]
               [--volume VOLUME] [--track TRACK] [--debug]
               input_file output_file

CLI application Transform MusicXML (*.mxl, *.xml, *.musicxml, *.midi) into OpenUTAU *.ustx for Singing Voice Synthesis

positional arguments:
  input_file            Input file to convert: [*.xml, *.musicxml, *.mxl, *.midi]
  output_file           Output file to create - example: outfile.ustx

options:
  -h, --help            show this help message and exit
  --project_name PROJECT_NAME
                        Name of the project, stored in the output file metadata
  --config_file CONFIG_FILE
                        Path to the config.yml file you want to use
  --track_config TRACK_CONFIG
                        Track config to use for this conversion, from config.yml
  --voice VOICE         Voice id used for each track, from config.yml
  --pan PAN             Pan setting used for each track (-100.0 to 100.0)
  --volume VOLUME       Volume setting used for each track (-10.0 to 10.0)
  --track TRACK         Name used for each track
  --debug               Print debug information

```
The `track_config` will always override the values defined by `--voice`, `--pan`, `--volume`, and `--track`. The latter can be specified multiple times on the command line to define the configuration for multiple tracks.

### Example
This application can be run via the included wrapper `run.sh`, which will also install the required python dependencies into a `venv` environment.
```
./run.sh infile.mxl outfile.ustx --track-config="ttbb-barbershop"
```

## Limitations
**There are MANY limitations.**
- No support for gradual tempo changes (e.g. ritardandos)
  - I think this can only be supported in USTX format by generating virtual tempo marker changes, since I do not think the format supports gradual changes. 
- Only supports tempos based on quarter-note length
- Lyrics MUST be defined on **ALL VOICES** on **ALL TRACKS**
  - This software makes no effort trying to guess the lyric based on other lines
- Lyrics broken across multiple notes are phonemized as individual words
  - I am unsure if there is any way to fix this problem since OpenUTAU handles phoneme generation internally

## Configuration
Voices and track presets are configured in `config.yml`. 

### Voice Presets
After installing new voices in OpenUTAU, you can add the voices as presets under the `voice_config` heading. There must always be a `default` voice. Voices will be referenced by `id`. This `id` is both used to cross-reference a voice in a `track_config` configuration, via `voice_id`. It is also the id used via the `--voice` CLI arguments.

You can determine the correct values to enter in this config by defining the voices in a blank OpenUTAU project, saving it as a file, and then inspecting the file in a text editor.

```
voice_config:
  - id: 'default'
    phonemizer: 'OpenUtau.Core.DefaultPhonemizer'
  - id: 'tiger'
    singer: 'TIGER_DS_v106'
    renderer: 'DIFFSINGER'
    phonemizer: 'OpenUtau.Core.DiffSinger.DiffSingerARPAPlusEnglishPhonemizer'
  - id: 'nero'
    singer: 'Nero_v110/configs'
    renderer: 'DIFFSINGER'
    phonemizer: 'OpenUtau.Core.DiffSinger.DiffSingerARPAPlusEnglishPhonemizer'
```

### Track Presets
Track presets can be made to automatically assign voices, volumes, names, and pans to the new OpenUTAU tracks, defined under the `track_config` heading. There must always be a `default` track config. These configs are referenced by `id` when using the `--track_config` CLI argument. All `voice_id` values must reference voices defined under the `voice_config` heading.

```
track_config:
  - id: 'default'
    tracks:
      - voice_id: 'default'
  - id: 'ttbb-barbershop'
    tracks:
      - track_name: 'Tenor'
        voice_id: 'tiger'
        pan: -60
        volume: 0
      - track_name: 'Lead'
        voice_id: 'tiger'
        pan: -25
        volume: 3
      - track_name: 'Bari'
        voice_id: 'tiger'
        pan: -60
        volume: 0
      - track_name: 'Bass'
        voice_id: 'nero'
        pan: 10
        volume: 6
```