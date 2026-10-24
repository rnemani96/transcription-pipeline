from transcriber.models import Chunk, PipelineError

CHUNK_SEC = 600
OVERLAP_SEC = 5
LONG_AUDIO_SEC = 900
MIN_TAIL_SEC = 1.0

def check_config(chunk_sec, overlap_sec, long_audio_sec):
    if chunk_sec <= 0:
        raise PipelineError("--chunk-sec must be greater than zero")
    if overlap_sec < 0:
        raise PipelineError("--overlap-sec cannot be negative")
    if long_audio_sec <= 0:
        raise PipelineError("--long-audio must be greater than zero")
    if chunk_sec >= long_audio_sec:
        raise PipelineError("--chunk-sec must be less than --long-audio")
    if overlap_sec >= chunk_sec:
        raise PipelineError("--overlap-sec must be less than --chunk-sec")


def plan_chunks(total_sec, chunk_sec, overlap_sec):
    if total_sec <= 0:
        raise PipelineError("audio duration must be greater than zero")
    if chunk_sec <= 0 or overlap_sec < 0:
        raise PipelineError("--chunk-sec must be greater than 0 and --overlap-sec cannot be negative")

    chunks, own_start = [], 0.0
    while own_start < total_sec:
        own_end = min(own_start + chunk_sec, total_sec)
        if total_sec - own_end < MIN_TAIL_SEC:
            own_end = total_sec
        chunks.append(Chunk(
            own_start=own_start,
            own_end=own_end,
            ext_start=max(0.0, own_start - overlap_sec),
            ext_end=min(total_sec, own_end + overlap_sec),
        ))
        own_start = own_end
    return chunks