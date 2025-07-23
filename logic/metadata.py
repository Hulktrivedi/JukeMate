# Mutagen Processor for Metadata

import os
import requests
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC
from PIL import Image
from io import BytesIO

def embed_metadata_flac(file_path, metadata, thumbnail_url):
    try:
        audio = FLAC(file_path)

        if 'title' in metadata:
            audio['title'] = metadata['title']
        if 'artist' in metadata:
            audio['artist'] = metadata['artist']
        if 'album' in metadata:
            audio['album'] = metadata['album']
        if 'release_year' in metadata:
            audio['date'] = metadata['release_year']

        # Download and embed album art
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                image = Image.open(image_data)
                img_format = image.format
                mime = f"image/{img_format.lower()}"

                pic = Picture()
                pic.data = response.content
                pic.type = 3  # front cover
                pic.mime = mime
                pic.desc = "Cover"
                audio.add_picture(pic)

        audio.save()
        return True
    except Exception as e:
        print(f"Metadata embedding failed: {e}")
        return False
