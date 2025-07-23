import tkinter as tk

def simple_slider(title, minval, maxval, default):
    slider_win = tk.Toplevel()
    slider_win.title(title)
    slider_win.configure(bg='#2e2e2e')

    label = tk.Label(slider_win, text=title, bg='#2e2e2e', fg='white')
    label.pack(pady=(10, 0))

    slider = tk.Scale(slider_win, from_=minval, to=maxval, resolution=0.1,
                      orient='horizontal', bg='#2e2e2e', fg='white', troughcolor='#444', highlightthickness=0)
    slider.set(default)
    slider.pack(pady=10)

    val = tk.DoubleVar()

    def submit():
        val.set(slider.get())
        slider_win.destroy()

    tk.Button(slider_win, text="OK", command=submit, bg="#444", fg="white", relief="flat").pack(pady=(0, 10))
    slider_win.wait_window()
    return val.get()
