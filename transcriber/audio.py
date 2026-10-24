import subprocess
from pathlib import Path

from transcriber.models import PipelineError

SAMPLE_RATE = 16000
ALLOWED = {".mp3", ".wav", ".m4a"}
MIN_DURATION_SEC = 0.5


def run(cmd):

    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        raise PipelineError(f"'{cmd[0]}' not found. Install ffmpeg and add it to PATH")
    except subprocess.CalledProcessError as e:
        raise PipelineError(f"'{cmd[0]}' failed: {e.stderr.strip()}")


def probe_duration(path):

    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)]).strip()
    try:
        return float(out)
    except ValueError:
        raise PipelineError(f"'{out}' is not a valid duration")


def validate_input(path):

    path = Path(path)
    if not path.is_file():
        raise PipelineError(f"'{path}' is not a file")
    if path.suffix.lower() not in ALLOWED:
        raise PipelineError(f"'{path}' has unsupported extension '{path.suffix}'")
    if path.stat().st_size == 0:
        raise PipelineError(f"'{path}' is empty")

    try:

        streams = run(["ffprobe", "-v", "error", "-select_streams", "a",
                       "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)])
        duration = probe_duration(path)
    except PipelineError as e:
        raise PipelineError(f"Cannot read {path.name} as audio: {e}")

    if not streams.strip():
        raise PipelineError(f"'{path.name}' contains no audio stream")
    if duration < MIN_DURATION_SEC:
        raise PipelineError(f"'{path.name}' is shorter than {MIN_DURATION_SEC} seconds")


def normalize(src, dst):

    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1",
         "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)])


def cut(wav, start, end, dst):
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", str(end - start),
         "-i", str(wav), "-c:a", "pcm_s16le", str(dst)])