import os
import subprocess
from yt_dlp import YoutubeDL
from logic.metadata import apply_metadata

# Define where FFmpeg is located
FFMPEG_PATH = r"C:\\ffmpeg-7.1.1\\ffmpeg-2025-05-26-git-43a69886b2-full_build\\bin"


def download_and_process(track_info, output_dir):
    """
    Downloads the audio, converts to FLAC, applies filters, and adds metadata.
    track_info = {
        'url': str,
        'title': str,
        'artist': str,
        'apply_hiss_removal': bool,
        'apply_balance': bool,
        'gain_db': float,
        'balance_adjustment': float
    }
    """
    try:
        # 1. Set download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': FFMPEG_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'flac',
            }],
            'outtmpl': os.path.join(output_dir, f"%(title)s.%(ext)s"),
            'quiet': True,
            'no_warnings': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_info['url'], download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.flac')

        filtered_file = filename.replace('.flac', '_filtered.flac')
        filters = []

        if track_info.get('apply_hiss_removal'):
            filters.append('highpass=f=200, lowpass=f=12000')

        if track_info.get('apply_balance') and track_info['balance_adjustment'] != 0.0:
            # panning both channels equally if needed
            left = 1.0 - abs(track_info['balance_adjustment']) if track_info['balance_adjustment'] < 0 else 1.0
            right = 1.0 - abs(track_info['balance_adjustment']) if track_info['balance_adjustment'] > 0 else 1.0
            pan_filter = f"pan=stereo|c0=c0*{left}|c1=c1*{right}"
            filters.append(pan_filter)

        if track_info['gain_db'] != 0.0:
            filters.append(f"volume={track_info['gain_db']}dB")

        filter_str = ','.join(filters)

        if filter_str:
            command = [
                os.path.join(FFMPEG_PATH, "ffmpeg"),
                '-y',
                '-i', filename,
                '-af', filter_str,
                filtered_file
            ]
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(filename)  # remove original
            os.rename(filtered_file, filename)  # rename filtered to original

        # 2. Apply Metadata
        apply_metadata(filename, track_info)
        return filename

    except Exception as e:
        raise RuntimeError(f"Failed to download or process {track_info.get('title', 'unknown')}: {str(e)}")
