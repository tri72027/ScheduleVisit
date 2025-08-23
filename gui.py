import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import logging
from main import main
from logger import setup_logger

# Handler để redirect log vào Text widget
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

class BookingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Schedule Visit")
        self.geometry("800x400")

        # Input số ngày
        tk.Label(self, text="Limit Days:").pack()
        self.days_entry = tk.Entry(self)
        self.days_entry.insert(0, "10")
        self.days_entry.pack(pady=5)

        # Nút bắt đầu
        self.start_btn = tk.Button(
            self,
            text="Start",
            font=("Arial", 13),
            bg="#4CAF50",
            fg="white",
            command=self.start_action
        )
        self.start_btn.pack(pady=10)

        # Ô console log
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=15, state="normal")
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

        # Setup logger và redirect vào log_area
        self.logger = setup_logger()
        text_handler = TextHandler(self.log_area)
        text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(text_handler)

    def start_action(self):
        try:
            max_days = int(self.days_entry.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ")
            return
        threading.Thread(target=main, args=(max_days,), daemon=True).start()


if __name__ == "__main__":
    app = BookingApp()
    app.mainloop()
