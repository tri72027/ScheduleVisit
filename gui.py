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

        # Frame chứa input ngang hàng
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        label_font = ("Arial", 11, "bold")

        # Input Limit Days
        tk.Label(input_frame, text="Limit Days:", font=label_font).grid(row=0, column=0, padx=5, sticky="e")
        self.days_entry = tk.Entry(input_frame, width=10, font=("Arial", 11))
        self.days_entry.insert(0, "10")
        self.days_entry.grid(row=0, column=1, padx=5)

        # Input Max Retry Case
        tk.Label(input_frame, text="Max Retry Case:", font=label_font).grid(row=0, column=2, padx=5, sticky="e")
        self.retry_entry = tk.Entry(input_frame, width=10, font=("Arial", 11))
        self.retry_entry.insert(0, "5")
        self.retry_entry.grid(row=0, column=3, padx=5)

        # Nút bắt đầu
        self.start_btn = tk.Button(
            self,
            text="Start",
            font=("Arial", 13, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.start_action
        )
        self.start_btn.pack(pady=10)

        # Ô console log
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=15, state="normal", font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

        # Setup logger và redirect vào log_area
        self.logger = setup_logger()
        text_handler = TextHandler(self.log_area)
        text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(text_handler)

    def start_action(self):
        try:
            max_days = int(self.days_entry.get())
            max_retry_case = int(self.retry_entry.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ")
            return
        threading.Thread(target=main, args=(max_days, max_retry_case), daemon=True).start()


if __name__ == "__main__":
    app = BookingApp()
    app.mainloop()
