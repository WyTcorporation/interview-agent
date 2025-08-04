import tkinter as tk

class TopmostOverlay:
    def __init__(self):
        self.root = tk.Tk()

        self.root.geometry("300x100+300+300")
        self.root.configure(bg="black")
        self.root.attributes("-topmost", True)               # поверх усього
        self.root.overrideredirect(True)                     # без рамки

        self.label = tk.Label(
            self.root,
            text="🧙‍♂️ Overlay без рамки\nTopmost=True",
            font=("Segoe UI", 11),
            bg="black",
            fg="lime",
            justify="center"
        )
        self.label.pack(expand=True, fill="both")

        # Кнопка закриття — своя, бо немає рамки
        self.close_button = tk.Button(
            self.root, text="✖", command=self.root.destroy,
            font=("Segoe UI", 10), bg="darkred", fg="white"
        )
        self.close_button.place(relx=1.0, rely=0.0, anchor="ne", x=-6, y=6)

        # Дозволити перетягування
        self.offset_x = 0
        self.offset_y = 0
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

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
    TopmostOverlay().run()
