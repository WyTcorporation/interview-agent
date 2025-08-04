import tkinter as tk
import requests
import threading
import time

class OverlayListener:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="black")

        self.offset_x = 0
        self.offset_y = 0
        self.answer = ""

        self.label = tk.Label(
            self.root,
            text="🧠 Чекаю...",
            font=("Segoe UI", 11),
            bg="black",
            fg="lime",
            wraplength=300,
            justify="left"
        )
        self.label.pack(padx=10, pady=(10, 5))

        self.close_button = tk.Button(
            self.root, text="✖", command=self.root.destroy,
            font=("Segoe UI", 9), bg="darkred", fg="white"
        )
        self.close_button.pack(pady=(0, 10))

        # Drag support
        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.root.geometry("+100+100")

        # Start background updater
        threading.Thread(target=self.poll_latest, daemon=True).start()

    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f'+{x}+{y}')

    def poll_latest(self):
        while True:
            try:
                res = requests.get("http://localhost:8000/latest", timeout=2)
                if res.ok:
                    data = res.json()
                    if data["answer"] != self.answer:
                        self.answer = data["answer"]
                        self.label.config(text=f"🧠 {self.answer}")
            except Exception as e:
                self.label.config(text=f"⚠️ {e}")
            time.sleep(3)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    OverlayListener().run()
