import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, error
import yt_dlp

# ====== CONFIG =======
OUTPUT_FOLDER = os.path.join(os.path.expanduser("~"), "Music", "The Playlist")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ====== UTILS ========

def embed_metadata_flac(file_path, metadata):
    try:
        audio = FLAC(file_path)
    except Exception as e:
        print(f"Failed to load FLAC file for metadata embedding: {e}")
        return

    # Set tags
    for key, val in metadata.items():
        if val:
            audio[key] = val

    # Embed album art if given
    if metadata.get('album_art_path') and os.path.isfile(metadata['album_art_path']):
        with open(metadata['album_art_path'], 'rb') as img_f:
            pic = Picture()
            pic.data = img_f.read()
            pic.type = 3  # front cover
            pic.mime = "image/jpeg"
            audio.clear_pictures()
            audio.add_picture(pic)

    audio.save()


def run_ffmpeg_processing(input_path, output_path, balance_stereo, remove_hiss, gain_db=5):
    # Build ffmpeg command dynamically
    cmd = ['ffmpeg', '-y', '-i', input_path]

    filters = []
    if balance_stereo:
        # Balance stereo by averaging channels to mono then back to stereo (simple example)
        filters.append("pan=stereo|c0=(c0+c1)/2|c1=(c0+c1)/2")

    if remove_hiss:
        # Use a high-pass filter to cut very low frequencies (simple hiss removal)
        filters.append("highpass=f=200")

    if filters:
        filter_chain = ",".join(filters)
        cmd += ['-af', filter_chain]

    if gain_db != 0:
        cmd += ['-filter:a', f'volume={gain_db}dB']

    cmd.append(output_path)

    # Run the command and wait
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {process.stderr}")


# ====== APP =======

class MusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Downloader & Processor")
        self.geometry("800x600")
        self.dark_mode = True
        self.configure(bg="#121212")

        self.playlist = []  # List of dicts with song info and settings

        # UI Setup
        self.create_widgets()

        def apply_theme(self):
            bg = "#121212" if self.dark_mode else "white"
            fg = "white" if self.dark_mode else "black"
            self.configure(bg=bg)

            style = ttk.Style(self)
            style.theme_use('default')
            style.configure("Treeview",
                            background=bg,
                            foreground=fg,
                            fieldbackground=bg)
            style.map("Treeview",
                      background=[('selected', '#6a99ff')],
                      foreground=[('selected', 'white')])

            for child in self.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=bg)
                    for grandchild in child.winfo_children():
                        try:
                            if isinstance(grandchild, (tk.Label, tk.Button)):
                                grandchild.configure(bg=bg, fg=fg)
                            elif isinstance(grandchild, tk.Entry):
                                grandchild.configure(bg=bg if self.dark_mode else "white", fg=fg)
                        except:
                            pass

    def create_widgets(self):
        # Top frame: input link + download button + toggle theme
        top_frame = tk.Frame(self, bg=self['bg'])
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.link_var = tk.StringVar()
        tk.Label(top_frame, text="YouTube Link:", bg=self['bg'], fg="white").pack(side=tk.LEFT)
        self.link_entry = tk.Entry(top_frame, textvariable=self.link_var, width=60)
        self.link_entry.pack(side=tk.LEFT, padx=5)
        self.download_btn = tk.Button(top_frame, text="Download & Add", command=self.download_and_add)
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.theme_btn = tk.Button(top_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        # Playlist Treeview
        columns = ("title", "artist", "balance_stereo", "remove_hiss", "status")
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='extended')
        for col in columns:
            self.tree.heading(col, text=col.replace('_', ' ').title())
            self.tree.column(col, width=150, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add toggles to each row (using tags and clicks)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Process button and progress bar
        bottom_frame = tk.Frame(self, bg=self['bg'])
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        self.process_btn = tk.Button(bottom_frame, text="Process Selected", command=self.process_selected)
        self.process_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(bottom_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=10)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg = "#121212" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        self.configure(bg=bg)
        self.tree.configure(background=bg, foreground=fg, fieldbackground=bg)
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)
                for grandchild in child.winfo_children():
                    try:
                        if isinstance(grandchild, (tk.Label, tk.Button)):
                            grandchild.configure(bg=bg, fg=fg)
                        elif isinstance(grandchild, tk.Entry):
                            grandchild.configure(bg=bg if self.dark_mode else "white", fg=fg)
                    except:
                        pass

    def add_song_to_playlist(self, song_path, title="Unknown", artist="Unknown"):
        # Default toggles off, status = pending
        song_info = {
            "path": song_path,
            "title": title,
            "artist": artist,
            "balance_stereo": False,
            "remove_hiss": False,
            "status": "Pending"
        }
        self.playlist.append(song_info)
        self.refresh_playlist_view()

    def refresh_playlist_view(self):
        self.tree.delete(*self.tree.get_children())
        for idx, song in enumerate(self.playlist):
            vals = (song['title'], song['artist'],
                    "Yes" if song['balance_stereo'] else "No",
                    "Yes" if song['remove_hiss'] else "No",
                    song['status'])
            self.tree.insert("", "end", iid=str(idx), values=vals)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            col = self.tree.identify_column(event.x)
            idx = int(item)
            if col == '#3':  # balance_stereo col
                self.playlist[idx]['balance_stereo'] = not self.playlist[idx]['balance_stereo']
            elif col == '#4':  # remove_hiss col
                self.playlist[idx]['remove_hiss'] = not self.playlist[idx]['remove_hiss']
            self.refresh_playlist_view()

    def download_and_add(self):
        link = self.link_var.get().strip()
        if not link:
            messagebox.showerror("Error", "Please enter a YouTube link.")
            return
        self.download_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.download_thread, args=(link,), daemon=True).start()

    def download_thread(self, link):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'ffmpeg_location': r'C:\ffmpeg-7.1.1\ffmpeg-2025-05-26-git-43a69886b2-full_build\bin',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'flac',
                    'preferredquality': '0',  # 0 = best
                }],
                'outtmpl': os.path.join(r'C:\Users\Administrator\Music\The Playlist', '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.ydl_progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link)
                title = info.get('title', 'Unknown Title')
                artist = info.get('artist', 'Unknown Artist')
                filename = os.path.join(r'C:\Users\Administrator\Music\The Playlist', f"{title}.flac")
                self.add_song_to_playlist(filename, title=title, artist=artist)
                self.status_label.config(text=f"Downloaded: {title}")

        except Exception as e:
            self.status_label.config(text=f"Skipped: {link}")
            print(f"[ERROR] Failed to download {link}: {e}")
            with open("failed_downloads.txt", "a", encoding="utf-8") as log:
                log.write(f"{link} - {e}\n")

        finally:
            self.download_btn.config(state=tk.NORMAL)

    def ydl_progress_hook(self, d):
        # Optionally update progress bar here
        pass

    def process_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select songs to process.")
            return

        self.process_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.process_thread, args=(selected,), daemon=True).start()

    def process_thread(self, selected_items):
        total = len(selected_items)
        for idx, item in enumerate(selected_items, start=1):
            song_idx = int(item)
            song = self.playlist[song_idx]
            self.update_song_status(song_idx, "Processing")
            input_path = song['path']
            # Output temp file path to avoid overwrite during processing
            output_path = input_path.replace(".flac", "_proc.flac")
            try:
                run_ffmpeg_processing(
                    input_path,
                    output_path,
                    balance_stereo=song['balance_stereo'],
                    remove_hiss=song['remove_hiss'],
                    gain_db=5
                )
                # Replace original file with processed file
                os.replace(output_path, input_path)

                # Embed dummy metadata (you can expand this with UI inputs)
                embed_metadata_flac(input_path, {
                    'title': song['title'],
                    'artist': song['artist'],
                    # 'album_art_path': 'path/to/art.jpg',  # Add if available
                })

                self.update_song_status(song_idx, "Done")
            except Exception as e:
                self.update_song_status(song_idx, f"Error: {e}")
            self.progress['value'] = (idx / total) * 100
        self.process_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0

    def update_song_status(self, idx, status):
        self.playlist[idx]['status'] = status
        self.refresh_playlist_view()


if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()
