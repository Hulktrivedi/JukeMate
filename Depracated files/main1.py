import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import yt_dlp
from mutagen.flac import FLAC
import subprocess

FFMPEG_PATH = r"C:\ffmpeg-7.1.1\ffmpeg-2025-05-26-git-43a69886b2-full_build\bin"
OUTPUT_FOLDER = r"C:\\Users\\Administrator\\Music\\The Playlist"


class Song:
    def __init__(self, url, title):
        self.url = url
        self.title = title
        self.download = tk.BooleanVar(value=False)
        self.hiss_removal = tk.BooleanVar(value=False)
        self.stereo_balance = tk.DoubleVar(value=0.0)
        self.gain = tk.DoubleVar(value=0.0)


class MusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Playlist Downloader")
        self.geometry("1000x600")

        self.songs = []

        self.setup_widgets()

    def select_all_downloads(self):
        for i, song in enumerate(self.songs):
            song.download.set(True)
            item_id = self.tree.get_children()[i]
            self.tree.set(item_id, "Download", "✔")

    def setup_widgets(self):
        self.link_entry = tk.Entry(self, width=70)
        self.link_entry.pack(pady=10)

        fetch_btn = tk.Button(self, text="Load Playlist", command=self.load_playlist)
        fetch_btn.pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("Title", "Download", "Hiss", "Stereo", "Gain"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Download", text="Download")
        self.tree.heading("Hiss", text="Hiss Remove")
        self.tree.heading("Stereo", text="Stereo Balance")
        self.tree.heading("Gain", text="Gain")
        self.tree.column("Title", width=300)
        self.tree.pack(expand=True, fill="both")
        select_all_btn = tk.Button(self, text="Select All for Download", command=self.select_all_downloads)
        select_all_btn.pack(pady=5)
        self.tree.bind("<Double-1>", self.on_tree_click)

        start_btn = tk.Button(self, text="Start Downloading", command=self.start_downloading)
        start_btn.pack(pady=10)

    def load_playlist(self):
        playlist_url = self.link_entry.get().strip()
        if not playlist_url:
            messagebox.showerror("Error", "Please enter a playlist URL or video URL.")
            return

        def fetch():
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(playlist_url, download=False)
                    entries = info.get('entries', None)
                    if entries is None:
                        # Single video case
                        title = info.get('title', 'Unknown Title')
                        url = info.get('webpage_url', playlist_url)
                        song = Song(url, title)
                        self.songs.append(song)
                        self.tree.insert('', 'end', values=(title, "✘", "✘", "0", "0"))
                    else:
                        # Playlist case
                        for entry in entries:
                            title = entry.get('title', 'Unknown Title')
                            url = entry.get('webpage_url', '')
                            song = Song(url, title)
                            self.songs.append(song)
                            self.tree.insert('', 'end', values=(title, "✘", "✘", "0", "0"))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=fetch).start()

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item:
            return

        index = self.tree.index(item)
        song = self.songs[index]

        if column == '#2':
            val = not song.download.get()
            song.download.set(val)
            self.tree.set(item, "Download", "✔" if val else "✘")

        elif column == '#3':
            val = not song.hiss_removal.get()
            song.hiss_removal.set(val)
            self.tree.set(item, "Hiss", "✔" if val else "✘")

        elif column == '#4':
            new_val = simple_slider("Stereo Balance (-1 to 1)", -1, 1, song.stereo_balance.get())
            song.stereo_balance.set(new_val)
            self.tree.set(item, "Stereo", f"{new_val:.1f}")

        elif column == '#5':
            new_val = simple_slider("Gain Adjustment (dB)", -10, 10, song.gain.get())
            song.gain.set(new_val)
            self.tree.set(item, "Gain", f"{new_val:.1f}")

    def start_downloading(self):
        for i, song in enumerate(self.songs):
            if song.download.get():
                threading.Thread(target=self.download_song, args=(song, i)).start()

    def download_song(self, song, index):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'ffmpeg_location': FFMPEG_PATH,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'flac',
                    'preferredquality': '320',
                }],
                'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song.url)
                filename = os.path.join(OUTPUT_FOLDER, f"{info['title']}.flac")

            self.apply_filters(filename, song)

        except Exception as e:
            messagebox.showerror("Download Error", f"{song.title}: {e}")

    def apply_filters(self, filename, song):
        cmd = [os.path.join(FFMPEG_PATH, 'ffmpeg'), '-y', '-i', filename]
        if song.hiss_removal.get():
            cmd.extend(['-af', 'afftdn'])

        if song.stereo_balance.get() != 0.0:
            pan_val = song.stereo_balance.get()
            cmd.extend(['-af', f"pan=stereo|c0=0.5*c0+{pan_val}*c1|c1=0.5*c1-{pan_val}*c0"])

        if song.gain.get() != 0.0:
            cmd.extend(['-af', f"volume={song.gain.get()}dB"])

        temp_file = filename.replace('.flac', '_filtered.flac')
        cmd.extend([temp_file])

        subprocess.run(cmd)

        os.replace(temp_file, filename)
        audio = FLAC(filename)
        audio.save()


def simple_slider(title, minval, maxval, default):
    slider_win = tk.Toplevel()
    slider_win.title(title)
    slider = tk.Scale(slider_win, from_=minval, to=maxval, resolution=0.1, orient='horizontal')
    slider.set(default)
    slider.pack()
    val = tk.DoubleVar()

    def submit():
        val.set(slider.get())
        slider_win.destroy()

    tk.Button(slider_win, text="OK", command=submit).pack()
    slider_win.wait_window()
    return val.get()


if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()
