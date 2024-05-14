from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Callable, Generic, Iterator, TypeVar, TypedDict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ParamT = TypeVar('ParamT')

class BaseCroniclePluginInput(BaseModel, Generic[ParamT]):
    id: str
    hostname: str
    command: Path
    event: str
    now: datetime
    log_file: Path
    params: ParamT

class ReportedProgress(TypedDict):
    progress: float
    perf: dict[str, float]


Runnable = Callable[[ParamT], Iterator[ReportedProgress]]

class BaseCroniclePlugin(Generic[ParamT]):
    def __init__(self, runnable: Runnable[ParamT], inputs: BaseCroniclePluginInput[ParamT]) -> None:
        self._runnable = runnable
        self._inputs = inputs

    def _log_progress_with_elapsed_time(self, reported_progress: ReportedProgress):
        print(json.dumps(reported_progress))

    def _log_complete(self, is_errored: bool):
        payload = {'complete': 1, 'code': int(is_errored)}
        print(json.dumps(payload))

    def run(self):
        try:
            for reported_progress in self._runnable(self._inputs.params):
                self._log_progress_with_elapsed_time(reported_progress)

            self._log_complete(is_errored=False)

        except Exception as e:
            logger.exception(e)
            self._log_complete(is_errored=True)
