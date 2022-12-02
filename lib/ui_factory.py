from contextlib import contextmanager
from dataclasses import dataclass
from rich.progress import Progress, TaskID, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

@dataclass
class ProgressListener:
    layout: Table
    overall_progress: Progress
    overall_task: TaskID

@contextmanager
def undeterminate_transient_progress(description: str, progress: Progress):
    task_id = progress.add_task(description, total=None)
    yield
    progress.stop_task(task_id)
    progress.update(task_id, visible=False)

class ProgressUIFactory:
    @staticmethod
    def create_process_listener():
        overall_progress = ProgressUIFactory.create_overall_progress()
        overall_task = overall_progress.add_task("All Jobs")

        progress_table = Table.grid(expand=True)
        progress_table.add_row(Panel(overall_progress, title="Overall Progress", border_style="green"))

        return ProgressListener(progress_table, overall_progress, overall_task)

    @staticmethod
    def create_overall_progress():
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            expand=True,
            transient=True
        )

    @staticmethod
    def create_job_progress():
        return Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True,
            transient=True
        )

    @staticmethod
    def create_job_panel(job_progress: Progress, job_id: int):
        return Panel(job_progress, title=f"[b]Job {job_id}", border_style="red")

    @staticmethod
    def create_job_panel_row_from_job_progress(layout: Table, job_progresses: list[Progress]):
        subtable = Table.grid()
        subtable.add_row(*[ProgressUIFactory.create_job_panel(job_progress, index)
                         for index, job_progress in enumerate(job_progresses)])
        layout.add_row(subtable)
