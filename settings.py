from typing import Optional
from pydantic import BaseModel, BaseSettings
from pydantic.types import DirectoryPath, FilePath, PositiveInt


class PathSettings(BaseModel):
    movies_folder: DirectoryPath
    series_folder: DirectoryPath
    backup_folder: DirectoryPath
    title_strategies: Optional[FilePath]
    title_re_blacklist: Optional[FilePath]


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


class Settings(BaseSettings):
    Paths: PathSettings
    Archive: Optional[ArchiveSettings]
    SegmentDetection: Optional[SegmentDetectionSettings]
    Processor: Optional[ProcessorSettings]
    Logger:Optional[LoggerSettings]

    class Config:
        env_nested_delimiter = '__'
