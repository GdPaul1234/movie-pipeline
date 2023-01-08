from dataclasses import dataclass
from typing import Any, cast
import PySimpleGUI as sg
import vlc


@dataclass
class VlcPlayer:
    player: Any
    list_player: Any
    media_player: Any


def create_vlc_player(window: sg.Window) -> VlcPlayer:
    # source: https://github.com/oaubert/python-vlc/blob/master/examples/psgvlc.py
    inst = cast(vlc.Instance, vlc.Instance())

    list_player = inst.media_list_player_new()
    media_list = inst.media_list_new([])

    list_player.set_media_list(media_list)
    player = list_player.get_media_player()

    # tell VLC where to render the video(s)
    tk_id = window['-VID_OUT-'].Widget.winfo_id()

    if sg.running_linux():
        player.set_xwindow(tk_id)
    elif sg.running_windows():
        player.set_hwnd(tk_id)
    else:  # running trinket, etc.
        player.set_hwnd(tk_id)  # TBD

    return VlcPlayer(player, list_player, media_list)
