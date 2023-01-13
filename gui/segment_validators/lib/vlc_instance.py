from typing import cast
import PySimpleGUI as sg
import vlc


def create_vlc_player(window: sg.Window) -> vlc.MediaPlayer:
    # source: https://github.com/oaubert/python-vlc/blob/master/examples/psgvlc.py
    player = cast(vlc.MediaPlayer, vlc.MediaPlayer())

    # tell VLC where to render the video(s)
    tk_id = window['-VID-OUT-'].Widget.winfo_id()

    if sg.running_linux():
        player.set_xwindow(tk_id)
    elif sg.running_windows():
        player.set_hwnd(tk_id)
    else:  # running trinket, etc.
        player.set_hwnd(tk_id)  # TBD

    return player
