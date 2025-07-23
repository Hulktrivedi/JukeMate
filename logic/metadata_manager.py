import os
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.mp3 import EasyMP3
from urllib.request import urlopen
from io import BytesIO

class MetadataManager:
    @staticmethod
    def set_flac_metadata(file_path, title=None, artist=None, album=None, year=None, album_art_url=None):
        if not file_path.lower().endswith(".flac"):
            return

        audio = FLAC(file_path)
        if title: audio["title"] = title
        if artist: audio["artist"] = artist
        if album: audio["album"] = album
        if year: audio["date"] = year

        if album_art_url:
            try:
                image_data = urlopen(album_art_url).read()
                picture = Picture()
                picture.data = image_data
                picture.type = 3  # Cover (front)
                picture.mime = "image/jpeg"  # or image/png
                picture.desc = "Cover"
                audio.clear_pictures()
                audio.add_picture(picture)
            except Exception as e:
                print(f"Failed to embed album art: {e}")

        audio.save()

    @staticmethod
    def set_mp3_metadata(file_path, title=None, artist=None, album=None, year=None, album_art_url=None):
        if not file_path.lower().endswith(".mp3"):
            return

        audio = EasyMP3(file_path)
        if title: audio["title"] = title
        if artist: audio["artist"] = artist
        if album: audio["album"] = album
        if year: audio["date"] = year
        audio.save()

        if album_art_url:
            try:
                id3 = ID3(file_path)
                image_data = urlopen(album_art_url).read()
                id3.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=image_data
                ))
                id3.save()
            except ID3Error as e:
                print(f"Failed to embed album art: {e}")
