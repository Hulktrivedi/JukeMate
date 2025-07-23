import tkinter as tk
from tkinter import ttk, messagebox
import threading
from logic.downloader import load_playlist, download_song, Song

class MusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Playlist Downloader")
        self.geometry("1000x600")

        self.songs = []

        self.setup_widgets()

    def setup_widgets(self):
        self.link_entry = tk.Entry(self, width=70)
        self.link_entry.pack(pady=10)

        fetch_btn = tk.Button(self, text="Load Playlist", command=self.load_playlist_ui)
        fetch_btn.pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("Title", "Download", "Hiss", "Stereo", "Gain"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Download", text="Download")
        self.tree.heading("Hiss", text="Hiss Remove")
        self.tree.heading("Stereo", text="Stereo Balance")
        self.tree.heading("Gain", text="Gain")
        self.tree.column("Title", width=300)
        self.tree.pack(expand=True, fill="both")

        self.tree.bind("<Double-1>", self.on_tree_click)

        self.status_label = tk.Label(self, text="0 songs loaded | 0 selected", anchor='w')
        self.status_label.pack(fill='x')

        start_btn = tk.Button(self, text="Start Downloading", command=self.start_downloading)
        start_btn.pack(pady=10)

    def update_status_label(self):
        total = len(self.songs)
        selected = sum(1 for s in self.songs if s.download.get())
        self.status_label.config(text=f"{total} songs loaded | {selected} selected")

    def load_playlist_ui(self):
        url = self.link_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a playlist URL.")
            return

        def fetch():
            try:
                self.songs.clear()
                for i in self.tree.get_children():
                    self.tree.delete(i)

                results = load_playlist(url)
                for title, link in results:
                    song = Song(link, title)
                    self.songs.append(song)
                    self.tree.insert('', 'end', values=(title, "✔", "✘", "0", "0"))
                    self.update_status_label()
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
            self.update_status_label()

        elif column == '#3':
            val = not song.hiss_removal.get()
            song.hiss_removal.set(val)
            self.tree.set(item, "Hiss", "✔" if val else "✘")

        elif column == '#4':
            from ui.slider import simple_slider
            new_val = simple_slider("Stereo Balance (-1 to 1)", -1, 1, song.stereo_balance.get())
            song.stereo_balance.set(new_val)
            self.tree.set(item, "Stereo", f"{new_val:.1f}")

        elif column == '#5':
            from ui.slider import simple_slider
            new_val = simple_slider("Gain Adjustment (dB)", -10, 10, song.gain.get())
            song.gain.set(new_val)
            self.tree.set(item, "Gain", f"{new_val:.1f}")

    def start_downloading(self):
        for song in self.songs:
            if song.download.get():
                threading.Thread(target=download_song, args=(song,)).start()
