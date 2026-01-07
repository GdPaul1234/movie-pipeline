import shutil
from typing import Literal, Optional

from pydantic import BaseModel
from pydantic.types import DirectoryPath, FilePath, PositiveInt, PositiveFloat
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathSettings(BaseModel):
    movies_folder: DirectoryPath
    series_folder: DirectoryPath
    backup_folder: DirectoryPath


class ArchiveSettings(BaseModel):
    base_backup_path: DirectoryPath
    movies_archive_folder: DirectoryPath
    max_retention_in_s: PositiveInt


class SegmentDetectionSettings(BaseModel):
    templates_path: Optional[DirectoryPath] = None
    segments_min_gap: PositiveFloat = 10.0
    segments_min_duration: PositiveFloat = 120.0
    match_template_threshold: PositiveFloat = 0.8
    padding_duration: PositiveFloat = 1800.0


class ProcessorSettings(BaseModel):
    nb_worker: PositiveInt
    xyops_process_file_event_id: Optional[str] = None


class LoggerSettings(BaseModel):
    file_path: FilePath


HwAccel = Literal['cuda', 'none']
VideoCodec = Literal['h264', 'hevc']


class Settings(BaseSettings):
    Paths: PathSettings
    Archive: Optional[ArchiveSettings] = None
    SegmentDetection: SegmentDetectionSettings = SegmentDetectionSettings()
    Processor: Optional[ProcessorSettings] = None
    Logger: Optional[LoggerSettings] = None

    ffmpeg_path: FilePath = shutil.which('ffmpeg')  # type: ignore
    ffmpeg_hwaccel: HwAccel = 'none'
    ffmpeg_vcodec: VideoCodec = 'h264'

    model_config = SettingsConfigDict(env_nested_delimiter='__')
