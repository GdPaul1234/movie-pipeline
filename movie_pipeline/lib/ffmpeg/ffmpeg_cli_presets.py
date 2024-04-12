from ...settings import HwAccel


def get_ffprefixes(hw_accel: HwAccel):
    return ["-hwaccel", hw_accel] if hw_accel != 'none' else []


def get_ffencode_video_params(hw_accel: HwAccel):
    if hw_accel == 'cuda':
        return {'vcodec': 'h264_nvenc', 'preset:v': 'p7', 'tune:v': 'hq', 'rc:v': 'vbr', 'cq:v': 28, 'profile:v': 'high'}
    else:
        return {'vcodec': 'libx264', 'preset': 'slow', 'tune': 'film', 'crf': 23, 'profile:v': 'high'}


def get_ffencode_audio_params():
    return {'acodec': 'aac', 'cutoff': '20K', 'audio_bitrate': '256K', 'ac':2}
