from dataclasses import dataclass

class PipelineError(Exception):
    pass


@dataclass
class Segment:
    start: float
    end: float
    text: str