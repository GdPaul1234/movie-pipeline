from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ....settings import Settings
from ..controllers.import_segments_from_file import SegmentImporter
from ..lib.simple_video_only_player import SimpleVideoOnlyPlayerConsumer
from ..lib.video_player import IVideoPlayer
from ..models.segment_container import Segment, SegmentContainer


class SegmentValidatorContext(BaseModel):
    segment_container = SegmentContainer()
    media_player: IVideoPlayer
    selected_segments: list[Segment] = []
    filepath: Path
    imported_segments: dict[str, str]
    config: Settings

    @property
    def position(self) -> float:
        return self.media_player.position

    @property
    def duration(self) -> float:
        return self.media_player.duration

    @classmethod
    def init_context(cls, filepath: Path, config: Settings):
        media_player = SimpleVideoOnlyPlayerConsumer(filepath)
        imported_segments = SegmentImporter(filepath).import_segments()

        return cls(
            media_player=media_player,
            filepath=filepath,
            imported_segments=imported_segments,
            config=config
        )


class TimelineSegment(BaseModel):
    fid: Any
    value: Segment


class TimelineContext(BaseModel):
    position_handle: Any = None
    segments: list[TimelineSegment] = []
