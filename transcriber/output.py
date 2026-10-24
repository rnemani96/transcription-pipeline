
import json
import re
from pathlib import Path

from transcriber.models import Segment


FILLERS = re.compile(r"\b(um+|uh+|erm)\b,?\s*", re.IGNORECASE)


def clean_text(text):

    text = FILLERS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([.,!?])", r"\1", text)


def build_result(src, segments, duration, clean=False):

    if clean:
        segments = [Segment(s.start, s.end, clean_text(s.text)) for s in segments]
        segments = [s for s in segments if re.search(r"\w", s.text)]
    return {
        "source": Path(src).name,
        "duration_sec": round(duration, 2),
        "cleaned": clean,
        "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segments],
        "full_text": " ".join(s.text for s in segments),
        "stats": {"segments": len(segments), "words": sum(len(s.text.split()) for s in segments)},
    }


def write_output(result, out_dir, stem):

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")