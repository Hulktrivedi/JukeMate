import subprocess
import os

def apply_audio_filters(input_file, output_file, reduce_hiss=False, balance_correction=0.0, gain_db=0.0):
    try:
        filters = []

        # Basic hiss reduction using a lowpass filter
        if reduce_hiss:
            filters.append("afftdn=nf=-25")

        # Stereo balance (simulate by adjusting channel volume)
        if balance_correction != 0.0:
            if balance_correction > 0:
                filters.append(f"pan=stereo|c0=0.8*c0|c1={1 + balance_correction}*c1")
            else:
                filters.append(f"pan=stereo|c0={1 - balance_correction}*c0|c1=0.8*c1")

        # Gain control
        if gain_db != 0.0:
            filters.append(f"volume={gain_db}dB")

        filter_chain = ','.join(filters) if filters else 'anull'

        command = [
            "ffmpeg", "-y", "-i", input_file,
            "-af", filter_chain,
            output_file
        ]

        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error applying filters to {input_file}: {e}")
        return False
