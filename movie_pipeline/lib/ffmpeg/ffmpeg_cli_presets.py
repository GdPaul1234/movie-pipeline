from ...settings import HwAccel, VideoCodec


def get_ffprefixes(hw_accel: HwAccel):
    return ["-hwaccel", hw_accel] if hw_accel != 'none' else []


def get_ffencode_video_params(hw_accel: HwAccel, vcodec: VideoCodec):
    match (vcodec, hw_accel):
        case ('h264', 'cuda'):
            return {'vcodec': 'h264_nvenc', 'preset:v': 'p7', 'tune:v': 'hq', 'rc:v': 'vbr', 'cq:v': 28, 'profile:v': 'high'}
        case ('h264', 'none'):
            # cf https://trac.ffmpeg.org/wiki/Encode/H.264
            return {'vcodec': 'libx264', 'preset': 'slow', 'tune': 'film', 'crf': 23, 'profile:v': 'high'}
        case ('hevc', 'cuda'):
            # cf https://www.technomancer.com/archives/74
            return {'vcodec': 'hevc_nvenc', 'preset': 'slow', 'rc-lookahead:v': 32, 'spatial_aq': 1, 'cq:v': 29, 'profile:v': 'main10'}
        case ('hevc', 'none'):
            # cf https://trac.ffmpeg.org/wiki/Encode/H.265
            return {'vcodec': 'libx265', 'preset': 'slow', 'crf': 28, 'profile:v': 'main'}

def get_ffencode_audio_params():
    return {'acodec': 'aac', 'cutoff': '20K', 'audio_bitrate': '256K', 'ac':2}
