import tkinter as tk
import win32gui
import win32con
import keyboard

class ToggleOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("320x100+300+300")
        self.root.configure(bg="black")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.label = tk.Label(
            self.root,
            text="🧙‍♂️ Overlay\nF2 → режим невидимості",
            font=("Segoe UI", 11),
            bg="black",
            fg="lime",
            justify="center"
        )
        self.label.pack(expand=True, fill="both")

        self.close_button = tk.Button(
            self.root, text="✖", command=self.root.destroy,
            font=("Segoe UI", 10), bg="darkred", fg="white"
        )
        self.close_button.place(relx=1.0, rely=0.0, anchor="ne", x=-6, y=6)

        self.offset_x = 0
        self.offset_y = 0
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.hwnd = self.root.winfo_id()
        self.transparent_mode = False

        self.enable_layered_with_alpha()
        keyboard.add_hotkey("F2", self.toggle_transparency)

    def enable_layered_with_alpha(self):
        """Встановлює WS_EX_LAYERED і прозорість через WinAPI"""
        styles = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        styles |= win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, styles)
        win32gui.SetLayeredWindowAttributes(
            self.hwnd, 0, int(0.85 * 255), win32con.LWA_ALPHA
        )

    def toggle_transparency(self):
        styles = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        if not self.transparent_mode:
            styles |= win32con.WS_EX_TRANSPARENT
            self.label.config(text="🕵️ Невидимий режим\nF2 — повернути")
        else:
            styles &= ~win32con.WS_EX_TRANSPARENT
            self.label.config(text="🧙‍♂️ Overlay\nF2 → режим невидимості")

        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, styles)
        self.transparent_mode = not self.transparent_mode

    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ToggleOverlay().run()
