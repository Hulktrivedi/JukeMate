import os
import subprocess

def apply_audio_filters(input_file, output_file, gain_db=0.0, balance=False, remove_hiss=False, ffmpeg_path='ffmpeg'):
    filters = []

    # Gain filter
    if gain_db != 0.0:
        filters.append(f"volume={gain_db}dB")

    # Balance stereo (convert to mono)
    if balance:
        filters.append("pan=mono|c0=0.5*c0+0.5*c1")

    # Remove hiss (lowpass filter)
    if remove_hiss:
        filters.append("afftdn=nf=-25")

    # Combine all filters
    filter_chain = ','.join(filters)

    command = [
        ffmpeg_path,
        '-i', input_file,
        '-af', filter_chain,
        '-y',  # Overwrite output file if exists
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing file {input_file}: {e}")
        return False
