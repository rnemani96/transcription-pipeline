
from transcriber.audio import probe_duration
from transcriber.models import Segment


class WhisperTranscriber:


    def __init__(self, model_size="small", language=None):

        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, compute_type="int8")
        self.language = language  # None = detect automatically

    def transcribe(self, wav):

        segs, _info = self.model.transcribe(
            str(wav),
            language=self.language,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return [Segment(s.start, s.end, s.text.strip()) for s in segs]


class MockTranscriber:

    def transcribe(self, wav):
        duration = probe_duration(wav)
        segments, t, i = [], 0.0, 0
        while t + 4 <= duration:
            segments.append(Segment(t, t + 4, f"um this is mock segment {i} uh"))
            t, i = t + 5, i + 1
        return segments