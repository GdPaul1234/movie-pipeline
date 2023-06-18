from abc import ABC
from pathlib import Path

import PySimpleGUI as sg


class IVideoPlayer(ABC):
    def __init__(self, source: Path) -> None:
        ...

    @property
    def position(self) -> float:
        ...

    @property
    def duration(self) -> float:
        ...

    def set_position(self, position: float, window: sg.Window) -> None:
        ...

    def set_relative_position(self, delta: float, window: sg.Window):
        ...
