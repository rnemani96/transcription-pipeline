"""Command-line entry point.

Examples:
  python main.py samples/talk.mp3 --model small --out output
  python main.py samples/talk.mp3 --mock          (fake engine, no model needed)
"""
import argparse
import logging
from pathlib import Path

from av.error import cls

from transcriber.audio import validate_input
from transcriber.chunking import CHUNK_SEC, LONG_AUDIO_SEC, OVERLAP_SEC, check_config
from transcriber.engine import MockTranscriber, WhisperTranscriber
from transcriber.models import PipelineError
from transcriber.output import build_result, write_output
from transcriber.pipeline import transcribe_file

log = logging.getLogger("main")


def main():
    ap = argparse.ArgumentParser(description="Transcribe an audio file to JSON.")
    ap.add_argument("audio", help="path to a WAV, MP3 or M4A file")
    ap.add_argument("--out", default="output", help="output folder (default: output)")
    ap.add_argument("--model", default="small", help="Whisper model size, e.g. tiny, base, small")
    ap.add_argument("--language", default="en", help="spoken language code (default: en)")
    ap.add_argument("--clean", action="store_true", help="remove filler words like um/uh")
    ap.add_argument("--chunk-sec", type=int, default=CHUNK_SEC)
    ap.add_argument("--overlap-sec", type=int, default=OVERLAP_SEC)
    ap.add_argument("--long-threshold", type=int, default=LONG_AUDIO_SEC)
    ap.add_argument("--mock", action="store_true", help="fake engine, no model needed")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        #Settings
        check_config(args.chunk_sec, args.overlap_sec, args.long_threshold)
        # Validating File
        validate_input(args.audio)

        # Running the engines
        if args.mock:
            engine = MockTranscriber()
        else:
            try:
                engine = WhisperTranscriber(args.model, args.language)
            except ImportError:
                raise PipelineError("faster-whisper is not installed. Run: pip install faster-whisper")
            except Exception as e:
                raise PipelineError(f"Could not load model '{args.model}': {e}")

        # Strating the Transcribing
        segments, duration = transcribe_file(args.audio, engine, args.chunk_sec,
                                             args.overlap_sec, args.long_threshold)
        result = build_result(args.audio, segments, duration, clean=args.clean)
        # Writting the output to json file
        write_output(result, args.out, stem=Path(args.audio).stem)
    except (PipelineError, OSError) as e:
        raise SystemExit(f"ERROR: {e}")

    log.info("done | %s", result["stats"])


if __name__ == "__main__":
    main()