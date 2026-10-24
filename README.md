# Transcription Pipeline

A small command-line tool that turns an audio file into a timestamped transcript (JSON).
It uses open-source Whisper (`faster-whisper`) running locally. A mock engine is included so the pipeline can be tested without downloading a model.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
# ffmpeg and ffprobe must be installed and on PATH
```

## Usage

```bash
python main.py samples/talk.mp3 --model small      # real transcription
python main.py samples/talk.mp3 --mock             # fake engine, no model needed
python main.py samples/talk.mp3 --clean            # remove "um" / "uh"
```

Output is written to `output/talk.json`.

| Flag | Default | Meaning |
|---|---|---|
| `--out` | `output` | Output folder |
| `--model` | `small` | Whisper model size (tiny, base, small, ...) |
| `--language` | `en` | Spoken language code |
| `--clean` | off | Remove filler words |
| `--chunk-sec` | 600 | Seconds of audio each chunk owns |
| `--overlap-sec` | 5 | Extra audio read on each side of a chunk |
| `--long-threshold` | 900 | Files up to this length run as one chunk |
| `--mock` | off | Use the fake engine |

Supported input: `.mp3`, `.wav`, `.m4a`.

## How it works

```
validate -> normalize -> chunk -> transcribe -> merge -> JSON
```

| Step | File | What it does |
|---|---|---|
| Validate | `transcriber/audio.py` | Checks the file exists, has a supported extension, is not empty, has audio, and is at least 0.5s long |
| Normalize | `transcriber/audio.py` | Converts the input to 16 kHz mono WAV with ffmpeg |
| Chunk | `transcriber/chunking.py` | Splits long audio into chunks with a few seconds of overlap |
| Transcribe | `transcriber/engine.py` | Runs each chunk through Whisper (or the mock) |
| Merge | `transcriber/pipeline.py` | Puts timestamps back on the original timeline and removes overlap duplicates |
| Output | `transcriber/output.py` | Builds and writes the JSON, optional filler cleanup |

## Design decisions

**1. Convert everything to one format first.**
Whisper requires 16 kHz mono audio. Converting every file once with FFmpeg standardizes the input, so the rest of the pipeline handles one consistent format without needing separate logic for different audio formats.

**2. Validate before doing expensive work.**
The pipeline follows four steps: load settings → validate the file → load the model → transcribe. This catches invalid flags and missing files before downloading the model. Expected errors print one `ERROR: ...` message and exit with a non-zero code, without a traceback.

**3. Split long audio into chunks.**
Long audio files are split into 10-minute chunks by default. This reduces memory usage and helps prevent Whisper from getting stuck in repetition loops during transcription.

**4. Overlap the chunks.**
Each chunk includes a few extra seconds of audio on both sides to avoid cutting words in half. For example, a chunk owns the 600–1200 second range but processes slightly beyond it. This ensures words near boundaries are heard completely while reducing duplicate transcription.

**5. Midpoint rule to avoid duplicates.**
Adjacent chunks share some audio overlap, so the same segment may appear in both. To prevent duplicates, a segment is kept only if its midpoint falls within that chunk’s assigned time range, ensuring each segment is counted only once.

**6. Shift timestamps by where the piece was cut.**
Whisper gives timestamps relative to each chunk. Adding the chunk's actual start time (`ext_start`) converts them to the original audio timeline, ensuring all segments have correct timestamps.

**7. Short files use the same code path.**
A file under `--long-threshold` is just one chunk. There is no separate branch for short files.

**8. Swappable engine.**
Any object with `transcribe(wav) -> list[Segment]` works. This is how the mock engine plugs in, and how another speech-to-text library could be used later.

**9. Whisper settings.**
`int8` for fast CPU inference with little accuracy loss. `vad_filter=True` skips silence, which reduces made-up text. `condition_on_previous_text=False` avoids repetition loops on long audio. The language is set (default English) instead of auto-detected, which keeps behavior predictable.

**10. Cleaning is optional.**
Original words are kept unless `--clean` is passed, and the JSON records a `cleaned` flag so a reader knows which version they have.

## Output format

```json
{
  "source": "talk.mp3",
  "duration_sec": 16.11,
  "cleaned": false,
  "segments": [{"start": 0.0, "end": 9.76, "text": "..."}],
  "full_text": "...",
  "stats": {"segments": 2, "words": 27}
}
```

## Testing

Mock run, forcing small chunks so the overlap logic is exercised:

```bash
ffmpeg -f lavfi -i "sine=frequency=440:duration=60" samples/tone60.mp3
python main.py samples/tone60.mp3 --mock --chunk-sec 20 --overlap-sec 5 --long-threshold 30
```

Expected: three chunks (0-20, 20-40, 40-60) and 12 segments in order.

Real run: a 16-second recording transcribed correctly with `--model small`.

## Known limitations

- **Boundary duplicates with real speech.** I tested the 16-second recording with deliberately tiny chunks (`--chunk-sec 8 --overlap-sec 2`). A sentence that crossed the chunk boundary was partly repeated, because Whisper splits the overlap into segments differently in each chunk, so the midpoint rule kept both. With the default 10-minute chunks this only affects sentences that happen to cross a boundary. The fix is word-level timestamps: keep only the words whose midpoint is inside each chunk's range, then rebuild the segments. I left it out to keep the code simple.
- `--clean` only handles English fillers (um, uh, erm).
- Whisper can invent text on near-silent audio. VAD filtering reduces this.
- Chunks run one after another, on CPU.


## Project layout

```
main.py
requirements.txt
transcriber/
    audio.py      # validate, normalize, cut
    chunking.py   # config checks and chunk planning
    engine.py     # Whisper and mock engines
    models.py     # Segment, Chunk, PipelineError
    output.py     # JSON building and filler cleanup
    pipeline.py   # the main flow
```
