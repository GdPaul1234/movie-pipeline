from typing import Optional
from pathlib import Path
from pydantic import BaseModel
from pydantic.types import DirectoryPath, FilePath, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathSettings(BaseModel):
    movies_folder: DirectoryPath
    series_folder: DirectoryPath
    backup_folder: DirectoryPath
    title_strategies: Optional[FilePath] = None
    title_re_blacklist: Optional[FilePath] = None


class ArchiveSettings(BaseModel):
    base_backup_path: DirectoryPath
    movies_archive_folder: DirectoryPath
    max_retention_in_s: PositiveInt


class SegmentDetectionSettings(BaseModel):
    templates_path: DirectoryPath


class ProcessorSettings(BaseModel):
    nb_worker: PositiveInt


class MediaDatabaseSettings(BaseModel):
    db_path: Path
    clean_after_update: bool = True


class LoggerSettings(BaseModel):
    file_path: FilePath


class Settings(BaseSettings):
    Paths: PathSettings
    Archive: Optional[ArchiveSettings] = None
    SegmentDetection: Optional[SegmentDetectionSettings] = None
    Processor: Optional[ProcessorSettings] = None
    MediaDatabase: Optional[MediaDatabaseSettings] = None
    Logger :Optional[LoggerSettings] = None

    model_config = SettingsConfigDict(env_nested_delimiter='__')
