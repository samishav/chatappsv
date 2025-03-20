import tkinter as tk
from tkinter import scrolledtext, messagebox
import pika
import threading

# 🔥 Gen Z Theme
BG_COLOR = "#121212"  
TEXT_COLOR = "#EEEEEE"  
ACCENT_COLOR = "#FF007F"  

# RabbitMQ setup
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "chat"

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gen Z Chat 💬")
        self.root.geometry("500x600")
        self.root.configure(bg=BG_COLOR)

        # Username input screen
        self.login_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.login_frame.pack(expand=True)

        tk.Label(self.login_frame, text="Enter Username", fg=TEXT_COLOR, bg=BG_COLOR, font=("Helvetica", 14)).pack(pady=10)
        self.username_entry = tk.Entry(self.login_frame, font=("Helvetica", 14), fg=TEXT_COLOR, bg="#222")
        self.username_entry.pack(pady=5)
        self.username_entry.focus()

        tk.Button(self.login_frame, text="Join Chat 🚀", font=("Helvetica", 14, "bold"),
                  bg=ACCENT_COLOR, fg=TEXT_COLOR, command=self.connect_chat).pack(pady=10)

    def connect_chat(self):
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showerror("Error", "Username cannot be empty!")
            return

        self.login_frame.destroy()
        self.setup_chat_ui()
        self.setup_rabbitmq()

    def setup_chat_ui(self):
        """Sets up the chat UI."""
        self.chat_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.chat_frame.pack(expand=True, fill="both")

        self.chat_box = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, font=("Helvetica", 12),
                                                  bg="#222", fg=TEXT_COLOR, state=tk.DISABLED)
        self.chat_box.pack(padx=10, pady=10, fill="both", expand=True)

        self.msg_entry = tk.Entry(self.chat_frame, font=("Helvetica", 14), bg="#333", fg=TEXT_COLOR)
        self.msg_entry.pack(padx=10, pady=5, fill="x")
        self.msg_entry.bind("<Return>", self.send_message)

        tk.Button(self.chat_frame, text="Send 💬", font=("Helvetica", 14, "bold"),
                  bg=ACCENT_COLOR, fg=TEXT_COLOR, command=self.send_message).pack(pady=10)

    def setup_rabbitmq(self):
        """Sets up RabbitMQ connection."""
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.queue_name = result.method.queue
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=self.queue_name)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self, event=None):
        """Sends a message."""
        message = self.msg_entry.get().strip()
        if message:
            self.channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", 
                                       body=f"{self.username}: {message}")
            self.msg_entry.delete(0, tk.END)

    def receive_messages(self):
        """Listens for messages."""
        def callback(ch, method, properties, body):
            message = body.decode()
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, f"{message}\n")
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.yview(tk.END)

        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
