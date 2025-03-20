import pika
import threading

class ChatClient:
    def __init__(self, username, host='localhost'):
        self.username = username
        self.host = host
        self.connection = None
        self.channel = None
        self.queue_name = None
        self.on_message_callback = None

    def connect(self):
        """Connect to RabbitMQ, declare an exchange and create a temporary queue."""
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange='chat_exchange', exchange_type='fanout')
            result = self.channel.queue_declare('', exclusive=True)
            self.queue_name = result.method.queue
            self.channel.queue_bind(exchange='chat_exchange', queue=self.queue_name)
            print("Connected to RabbitMQ.")
        except Exception as e:
            print("Connection failed:", e)

    def send_message(self, text):
        """Publish a message to the chat exchange."""
        if not self.connection:
            raise ConnectionError("Please connect first.")
        message = f"{self.username}: {text}"
        try:
            self.channel.basic_publish(exchange='chat_exchange', routing_key='', body=message)
        except Exception as e:
            print("Sending message failed:", e)

    def start_listening(self, callback):
        """Start a thread to listen for incoming messages using the provided callback."""
        if not self.connection:
            raise ConnectionError("Please connect first.")
        self.on_message_callback = callback
        threading.Thread(target=self._listen, daemon=True).start()
        print("Listening for messages...")

    def _listen(self):
        """Internal method to consume messages and call the callback."""
        def on_message(ch, method, properties, body):
            if self.on_message_callback:
                self.on_message_callback(body.decode('utf-8'))
        try:
            self.channel.basic_consume(queue=self.queue_name, on_message_callback=on_message, auto_ack=True)
            self.channel.start_consuming()
        except Exception as e:
            print("Error receiving messages:", e)

    def disconnect(self):
        """Disconnect from RabbitMQ and clean up."""
        if self.connection:
            try:
                self.connection.close()
                print("Disconnected from RabbitMQ.")
            except Exception as e:
                print("Disconnect failed:", e)
            finally:
                self.connection = None
                self.channel = None
                self.queue_name = None

# Console usage
if __name__ == "__main__":
    username = input("Enter username: ").strip() or "Anonymous"
    client = ChatClient(username)
    client.connect()
    client.start_listening(lambda msg: print("[Message]", msg))
    print("Type your messages (type '/exit' to quit):")
    while True:
        user_input = input()
        if user_input.lower() == "/exit":
            break
        client.send_message(user_input)
    client.disconnect()
    print("Client exited.")
