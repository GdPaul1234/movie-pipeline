import shutil
from typing import Literal, Optional

from pydantic import BaseModel
from pydantic.types import DirectoryPath, FilePath, PositiveInt
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
    templates_path: DirectoryPath


class ProcessorSettings(BaseModel):
    nb_worker: PositiveInt


class LoggerSettings(BaseModel):
    file_path: FilePath


HwAccel = Literal['cuda', 'none']


class Settings(BaseSettings):
    Paths: PathSettings
    Archive: Optional[ArchiveSettings] = None
    SegmentDetection: Optional[SegmentDetectionSettings] = None
    Processor: Optional[ProcessorSettings] = None
    Logger: Optional[LoggerSettings] = None

    ffmpeg_path: FilePath = shutil.which('ffmpeg')  # type: ignore
    ffmpeg_hwaccel: HwAccel = 'none'

    model_config = SettingsConfigDict(env_nested_delimiter='__')
