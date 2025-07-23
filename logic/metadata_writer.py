from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3NoHeaderError
import requests
import os

def embed_metadata_flac(file_path, title=None, artist=None, album=None, year=None, album_art_url=None):
    try:
        audio = FLAC(file_path)

        if title:
            audio['title'] = title
        if artist:
            audio['artist'] = artist
        if album:
            audio['album'] = album
        if year:
            audio['date'] = str(year)

        if album_art_url:
            pic = Picture()
            pic.type = 3  # Cover (front)
            pic.mime = 'image/jpeg' if album_art_url.endswith('.jpg') or album_art_url.endswith('.jpeg') else 'image/png'
            pic.desc = 'Cover'
            pic.data = requests.get(album_art_url).content
            audio.clear_pictures()
            audio.add_picture(pic)

        audio.save()
        return True

    except Exception as e:
        print(f"Metadata embedding failed for {file_path}: {
