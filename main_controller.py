import tkinter as tk
from tkinter import ttk, messagebox
from gui.track_row import TrackRow
from logic.downloader import download_selected_tracks
from logic.metadata import embed_metadata

class MusicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Music Library Builder")
        self.root.geometry("1000x600")
        self.root.configure(bg="#2e2e2e")

        self.track_rows = []

        self.build_ui()

    def build_ui(self):
        # Entry for playlist/single song URL
        self.url_entry = tk.Entry(self.root, width=70, font=("Segoe UI", 11))
        self.url_entry.pack(pady=(10, 5))

        # Load Button
        load_btn = tk.Button(self.root, text="Load Playlist/Song", command=self.load_links)
        load_btn.pack(pady=(0, 10))

        # Frame to contain track rows
        self.track_list_frame = tk.Frame(self.root, bg="#2e2e2e")
        self.track_list_frame.pack(fill="both", expand=True)

        # Scrollbar for the track list
        self.canvas = tk.Canvas(self.track_list_frame, bg="#2e2e2e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.track_list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2e2e2e")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Download Button
        download_btn = tk.Button(self.root, text="Start Download", command=self.start_download)
        download_btn.pack(pady=10)

    def load_links(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please paste a YouTube Music link.")
            return

        try:
            from logic.downloader import get_playlist_info
            tracks = get_playlist_info(url)

            # Clear previous entries
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.track_rows.clear()

            for index, track in enumerate(tracks):
                row = TrackRow(self.scrollable_frame, track, index)
                row.pack(fill="x", padx=10, pady=5)
                self.track_rows.append(row)

        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def start_download(self):
        to_download = [row.track for row in self.track_rows if row.should_download()]
        if not to_download:
            messagebox.showwarning("No Tracks Selected", "Please select at least one track to download.")
            return

        try:
            download_selected_tracks(to_download)
            messagebox.showinfo("Success", "Download and post-processing completed.")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))

if __name__ == '__main__':
    root = tk.Tk()
    app = MusicApp(root)
    root.mainloop()
