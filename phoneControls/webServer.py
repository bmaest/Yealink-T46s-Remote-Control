from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError
import base64, urllib.parse, time, json, os

PHONE_IP = ""
USERNAME = ""
PASSWORD = ""

def send_phone_command(command):
    encoded_command = urllib.parse.quote(command, safe='')
    url = f"http://{PHONE_IP}/servlet?key={encoded_command}"
    credentials = f"{USERNAME}:{PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = { "Authorization": f"Basic {encoded}" }
    print(f"[COMMAND] Sending: {command} → Encoded: {encoded_command}")
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=2) as response:
            print(f"[SERVER] Response Status: {response.status}")
            return response.status == 200
    except URLError as e:
        print(f"[SERVER] Error: {e}")
        return False

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"\n[SERVER] Raw GET request from {self.client_address[0]}")
        print(f"  Path: {self.path}")
        print("  Headers:")
        for key, value in self.headers.items():
            print(f"    {key}: {value}")

        path, _, query = self.path.partition("?")
        params = urllib.parse.parse_qs(query)

        if path == "/":
            self.serve_html("index.html")

        elif path == "/overlay":
            self.serve_html("overlay.html")

        elif path.startswith("/resources/"):
            self.serve_static_file(path[1:])

        elif path == "/toggle":
            success = send_phone_command("MUTE")
            self.respond_text("Mute toggled successfully." if success else "Mute toggle failed.")

        elif path == "/answer":
            success = send_phone_command("ANSWER")
            self.respond_text("Call answered." if success else "Answer failed.")

        elif path == "/reject":
            success = send_phone_command("CALLEND")
            self.respond_text("Call rejected." if success else "Reject failed.")

        elif path == "/hold":
            success = send_phone_command("HOLD")
            self.respond_text("Hold toggled successfully." if success else "Hold toggle failed.")

        elif path == "/transfer":
            target = params.get("target", [""])[0]
            if target:
                digits = ";".join(list(target))
                uri = f"F_CONFERENCE;{digits};ENTER"
                print(f"[TRANSFER] Sending URI: {uri}")
                success = send_phone_command(uri)
                self.respond_text(f"Transferred to {target}" if success else f"Transfer to {target} failed.")
            else:
                self.respond_text("No target specified.")

        elif path == "/call":
            target = params.get("target", [""])[0]
            if target.strip():
                sequence = ["DIAL"] + list(target) + ["ENTER"]
                print(f"[CALL] Sending digits one by one: {sequence}")

                for key in sequence:
                    success = send_phone_command(key)
                    print(f"[CALL] Sent: {key} → {'OK' if success else 'FAIL'}")
                    time.sleep(0.2)  # Delay between keypresses

                self.respond_text(f"Calling {target}")
            else:
                print("[CALL] No target provided — accepting incoming call")
                success = send_phone_command("ANSWER")
                self.respond_text("Incoming call answered." if success else "Failed to answer incoming call.")

        elif path == "/macro":
            sequence = params.get("sequence", [""])[0]
            if sequence:
                print(f"[MACRO] Executing sequence: {sequence}")
                success = send_phone_command(sequence)
                self.respond_text("Conference macro sent." if success else "Macro failed.")
            else:
                self.respond_text("No macro sequence provided.")

        elif path == "/dnd":
            mode = params.get("mode", [""])[0].lower()
            if mode == "on":
                success = send_phone_command("DNDOn")
                self.respond_text("DND enabled." if success else "Failed to enable DND.")
            elif mode == "off":
                success = send_phone_command("DNDOff")
                self.respond_text("DND disabled." if success else "Failed to disable DND.")
            else:
                self.respond_text("Invalid DND mode.")

        elif path == "/volume":
            direction = params.get("direction", [""])[0].lower()
            if direction == "up":
                success = send_phone_command("VOLUME_UP")
                self.respond_text("Volume increased." if success else "Failed to increase volume.")
            elif direction == "down":
                success = send_phone_command("VOLUME_DOWN")
                self.respond_text("Volume decreased." if success else "Failed to decrease volume.")
            else:
                self.respond_text("Invalid volume direction.")

        elif path == "/calls":
            try:
                with open("syslog/cid_status.json", "r") as f:
                    data = json.load(f)
                    calls = list(data.values())
            except Exception as e:
                print(f"[ERROR] Failed to read cid_status.json: {e}")
                calls = []

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(calls).encode("utf-8"))

    def serve_html(self, filename):
        try:
            with open(filename, "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, f"HTML file '{filename}' not found")

    def serve_static_file(self, filepath):
        full_path = os.path.join(os.getcwd(), filepath)
        if os.path.isfile(full_path):
            self.send_response(200)
            if filepath.endswith(".png"):
                self.send_header("Content-type", "image/png")
            elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
                self.send_header("Content-type", "image/jpeg")
            else:
                self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"File not found: {filepath}")

    def respond_text(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

if __name__ == "__main__":
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("[SERVER] Server running on port 8080...")
    httpd.serve_forever()
