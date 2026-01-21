#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import shutil
import socket
from datetime import datetime, timedelta
import json
from config import SERVER_NAME, VERSION, COPYRIGHT, HOST, PORT, REFRESH_SECONDS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return float(f.read()) / 1000.0
    except:
        return None


def read_uptime():
    try:
        with open("/proc/uptime") as f:
            seconds = int(float(f.read().split()[0]))
            return str(timedelta(seconds=seconds))
    except:
        return "unbekannt"


def read_load():
    try:
        return os.getloadavg()[0]
    except:
        return 0.0


def read_disk_usage():
    try:
        total, used, free = shutil.disk_usage("/")
        return f"{used / (1024**3):.1f} GB / {total / (1024**3):.1f} GB"
    except:
        return "unbekannt"


def get_ip_address():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "unbekannt"


def current_time():
    return datetime.now().strftime("%H:%M:%S")


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/status":
                temp = read_cpu_temp()
                if temp is None:
                    temp_display = "unbekannt"
                    temp_color = "#ffffff"
                else:
                    temp_display = f"{temp:.1f} °C"
                    if temp < 50:
                        temp_color = "#4caf50"
                    elif temp < 65:
                        temp_color = "#ff9800"
                    else:
                        temp_color = "#f44336"

                data = {
                    "TEMP": temp_display,
                    "TEMP_COLOR": temp_color,
                    "LOAD": f"{read_load():.2f}",
                    "UPTIME": read_uptime(),
                    "DISK": read_disk_usage(),
                    "IP": get_ip_address(),
                    "TIME": current_time()
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode("utf-8"))
                return

            # normale Seite
            html = load_file(os.path.join(TEMPLATE_DIR, "index.html"))
            css = load_file(os.path.join(STATIC_DIR, "style.css")).replace("{TEMP_COLOR}", "#ffffff")
            # HTML: Platzhalter werden **nicht per .format() ersetzt**, alles dynamisch via JS
            html = html.replace("{CSS}", css)
            html = html.replace("{SERVER_NAME}", SERVER_NAME)
            html = html.replace("{VERSION}", VERSION)
            html = html.replace("{YEAR}", str(datetime.now().year))
            html = html.replace("{COPYRIGHT}", COPYRIGHT)
            html = html.replace("{PORT}", str(PORT))
            html = html.replace("{REFRESH}", str(REFRESH_SECONDS))

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Server error: {e}".encode("utf-8"))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print(f"{SERVER_NAME} v{VERSION} on Port {PORT} is running.")
    print(f"(c) {datetime.now().year} {COPYRIGHT}")
    server = HTTPServer((HOST, PORT), StatusHandler)
    server.serve_forever()
