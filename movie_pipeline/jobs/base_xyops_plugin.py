from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Callable, Generic, Iterator, Literal, TypeVar, TypedDict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ParamT = TypeVar('ParamT')

class BaseXyOpsPluginInput(BaseModel, Generic[ParamT]):
    # event properties
    xy: int
    type: Literal['event']
    params: ParamT

    # job properties
    id: str
    command: Path
    event: str
    now: datetime
    log_file: Path

class ReportedProgress(TypedDict):
    xy: int
    progress: float
    perf: dict[str, float]


Runnable = Callable[[ParamT], Iterator[ReportedProgress]]

class BaseXyOpsPlugin(Generic[ParamT]):
    def __init__(self, runnable: Runnable[ParamT], inputs: BaseXyOpsPluginInput[ParamT]) -> None:
        self._runnable = runnable
        self._inputs = inputs

    def _log_progress_with_elapsed_time(self, reported_progress: ReportedProgress):
        print(json.dumps(reported_progress))

    def _log_complete(self, exception: Exception | None=None):
        payload = {}
        payload['xy'] = 1
        
        if exception is None:
            payload['code'] = 0
        else:
            payload['code'] = hash(type(exception))
            payload['description'] = str(exception)

        print(json.dumps(payload))

    def run(self):
        try:
            for reported_progress in self._runnable(self._inputs.params):
                self._log_progress_with_elapsed_time(reported_progress)

            self._log_complete()

        except Exception as e:
            logger.exception(e)
            self._log_complete(e)
