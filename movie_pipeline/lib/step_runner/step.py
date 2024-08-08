from abc import ABC
from dataclasses import dataclass, field
import time
from typing import Generic, Iterator, Optional, TypeVar


ContextT = TypeVar('ContextT')


@dataclass
class StepProgressResult:
    current_step_name: str = field(init=False)
    current_step: 'BaseStep'
    current_step_percent: float
    current_step_elapsed_time: float
    total_percent: float

    def __post_init__(self):
        self.current_step_name = type(self.current_step).__name__


@dataclass
class BaseStep(ABC, Generic[ContextT]):
    context: ContextT
    description: str
    cost: float
    next_step: Optional['BaseStep[ContextT]']

    @property
    def all_steps(self) -> list['BaseStep[ContextT]']:
        visited_steps: list[BaseStep[ContextT]] = []
        visited_step = self

        while visited_step is not None:
            visited_steps.append(visited_step)
            visited_step = visited_step.next_step

        return visited_steps

    @property
    def total_cost(self) -> float:
        return sum(step.cost for step in self.all_steps)

    def _before_perform(self) -> None:
        pass

    def _perform(self) -> Iterator[float]:
        ...

    def _after_perform(self) -> None:
        pass

    def handle(self) -> Iterator[tuple[float, float]]:
        start_time = time.perf_counter()
        self._before_perform()

        for progress_percent in self._perform():
            yield progress_percent, time.perf_counter() - start_time

        self._after_perform()
        yield 1, time.perf_counter() - start_time

    def process_all(self) -> Iterator[StepProgressResult]:
        total_cost = self.total_cost

        completed_percent = 0.0
        current_step = self

        while current_step is not None:
            total_normalized_current_cost = current_step.cost / float(total_cost) # (0..1)

            for progress_percent, progress_elapsed_time in current_step.handle():
                yield StepProgressResult(
                    current_step=current_step,
                    current_step_percent=progress_percent,
                    current_step_elapsed_time=progress_elapsed_time,
                    total_percent=completed_percent + total_normalized_current_cost * progress_percent
                )

            completed_percent += total_normalized_current_cost
            current_step = current_step.next_step
