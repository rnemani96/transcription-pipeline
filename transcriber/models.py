from dataclasses import dataclass

class PipelineError(Exception):
    pass


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Chunk:
    ext_start: float
    ext_end: float
    own_start: float
    own_end: float