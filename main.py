import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Health)
    server.serve_forever()


threading.Thread(target=run_server, daemon=True).start()

from bot import bot

if __name__ == "__main__":
    bot.infinity_polling()
