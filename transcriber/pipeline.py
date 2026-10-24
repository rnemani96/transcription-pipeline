
import logging
import tempfile
from pathlib import Path

from transcriber.audio import cut, normalize, probe_duration
from transcriber.chunking import CHUNK_SEC, LONG_AUDIO_SEC, OVERLAP_SEC, check_config, plan_chunks
from transcriber.models import Segment

log = logging.getLogger(__name__)


def transcribe_file(src, engine, chunk_sec=CHUNK_SEC, overlap_sec=OVERLAP_SEC, long_sec=LONG_AUDIO_SEC):

    check_config(chunk_sec, overlap_sec, long_sec)

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        normalize(src, wav)
        total = probe_duration(wav)

        size = total if total <= long_sec else chunk_sec

        segments = []
        for i, c in enumerate(plan_chunks(total, size, overlap_sec)):
            log.info("chunk %d: owns %.0f-%.0fs", i, c.own_start, c.own_end)
            piece = Path(tmp) / f"chunk_{i}.wav"
            cut(wav, c.ext_start, c.ext_end, piece)

            for s in engine.transcribe(piece):
                start, end = s.start + c.ext_start, s.end + c.ext_start
                middle = (start + end) / 2

                is_last = c.own_end >= total
                if c.own_start <= middle and (middle < c.own_end or is_last):
                    segments.append(Segment(round(start, 2), round(end, 2), s.text))

            piece.unlink()
        return segments, total