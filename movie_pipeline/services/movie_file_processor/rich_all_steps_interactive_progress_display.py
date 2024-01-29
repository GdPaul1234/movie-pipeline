from typing import TypedDict

from rich.progress import Progress, TaskID

from .movie_file_processor_step import BaseStep, StepProgressResult


def process_with_progress_tui(progress: Progress, movie_file_processor_root_step: BaseStep):
    progress_state_t = TypedDict('ProgressState', {'current_step': BaseStep | None, 'task_id': TaskID | None})
    state: progress_state_t = {'current_step': None, 'task_id': None}

    def stop_previous_task():
        if state['task_id'] is None: return
        progress.stop_task(state['task_id'])
        progress.update(state['task_id'], visible=False)

    def add_task_if_needed(step_progress_result: StepProgressResult):
        if step_progress_result.current_step != state['current_step']:
            stop_previous_task()
            state['current_step'] = step_progress_result.current_step
            state['task_id'] = progress.add_task(description=state['current_step'].description, total=1.0)

    def update_task(step_progress_result: StepProgressResult):
        if state['task_id'] is None: return
        progress.update(state['task_id'], completed=step_progress_result.current_step_percent)

    for step_progress_result in movie_file_processor_root_step.process_all():
        add_task_if_needed(step_progress_result)
        update_task(step_progress_result)
        yield step_progress_result.total_percent

    stop_previous_task()
