import tkinter as tk
from tkinter import ttk
from filter_config import parse_filters_for_track
from post_processing import apply_audio_filters, embed_metadata

class TrackRow:
    def __init__(self, master, track_info):
        self.frame = tk.Frame(master, bg='#2e2e2e')
        self.track_info = track_info
        self.selected = tk.BooleanVar(value=True)
        self.hiss_removal = tk.BooleanVar(value=False)
        self.balance = tk.BooleanVar(value=False)
        self.gain = tk.DoubleVar(value=0.0)

        self.checkbox = tk.Checkbutton(self.frame, variable=self.selected, bg='#2e2e2e')
        self.checkbox.grid(row=0, column=0)
        tk.Label(self.frame, text=track_info['title'], fg='white', bg='#2e2e2e').grid(row=0, column=1)
        tk.Checkbutton(self.frame, text='Hiss', variable=self.hiss_removal, bg='#2e2e2e', fg='white').grid(row=0, column=2)
        tk.Checkbutton(self.frame, text='Balance', variable=self.balance, bg='#2e2e2e', fg='white').grid(row=0, column=3)
        tk.Scale(self.frame, from_=-10, to=10, orient='horizontal', variable=self.gain,
                 resolution=0.5, length=100, bg='#2e2e2e', fg='white').grid(row=0, column=4)
        self.frame.pack(fill='x', pady=2)

    def get_filter_config(self):
        return parse_filters_for_track({
            'apply_hiss_removal': self.hiss_removal.get(),
            'apply_balance': self.balance.get(),
            'gain_db': self.gain.get()
        })

    def should_download(self):
        return self.selected.get()

    def get_metadata(self):
        return {
            'title': self.track_info['title'],
            'artist': self.track_info.get('artist', 'Unknown'),
            'year': self.track_info.get('year', '')
        }
