import asyncio
import random
import base64
import datetime
import os
import json
from aiocoap import *
from aiocoap import resource

LOG_FILE = "coap_honeypot.log"

def log_request(remote, method, path, payload):
    if remote.startswith("127.0.0.1"):
        return
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.datetime.now().isoformat()
        headers = getattr(payload, "opt", {})
        log_line = f"{timestamp}, {remote}, {method}, {path}, {payload.decode(errors='ignore')}, {headers}\n"
        f.write(log_line)



class TemperatureResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.temperature = 20.0
        asyncio.get_event_loop().create_task(self.update_temperature())

    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/temperature", b"")
        payload = f'{self.temperature:.2f} °C'.encode('utf8')
        return Message(payload=payload)

    async def update_temperature(self):
        protocol = await Context.create_client_context()
        while True:
            self.temperature = 20 + random.uniform(-3, 8)
            print(f"[TempSensor] Updated temperature: {self.temperature:.2f} °C")
            self.updated_state()
            if self.temperature > 25:
                print("[TempSensor] High temperature! Triggering camera action...")
                request = Message(code=Code.POST, uri="coap://localhost/camera", payload=b"start stream")
                try:
                    response = await protocol.request(request).response
                    print(f"[TempSensor] Camera responded: {response.payload.decode()}")
                except Exception as e:
                    print(f"[TempSensor] Failed to reach camera: {e}")
            await asyncio.sleep(60)

class CameraResource(resource.Resource):
    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/camera", b"")
        fake_image = base64.b64encode(b"Lalala fake camera image")
        print("[Camera] Sending image...")
        return Message(payload=fake_image)

    async def render_post(self, request):
        log_request(request.remote.hostinfo, "POST", "/camera", request.payload)
        print(f"[Camera] Received POST: {request.payload.decode(errors='ignore')}")
        ack = b"Camera stream started (simulated)"
        return Message(code=Code.CHANGED, payload=ack)

class DebugResource(resource.Resource):
    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/debug", b"")
        # Fuite d'informations sensibles
        debug_info = {
            "system": "OK",
            "temp": round(random.uniform(22, 30), 2),
            "firmware_version": "v1.2.3",
            "internal_ip": "192.168.10.15",
            "admin_panel": "http://admin:default@192.168.10.1:8080",
            "database_conn": "mysql://dbuser:dbpass@localhost/iot_data",
            "logs": "clear"
        }
        return Message(payload=json.dumps(debug_info).encode())

class FirmwareResource(resource.Resource):
    async def render_post(self, request):
        log_request(request.remote.hostinfo, "POST", "/firmware", request.payload)

        # Simuler une vulnérabilité de buffer overflow
        if len(request.payload) > 100:
            print("[ALERT] Possible firmware exploitation attempt detected!")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=b"Firmware upload failed (buffer overflow?)")

        return Message(code=Code.CHANGED, payload=b"Firmware uploaded successfully")

# Nouveaux endpoints attrayants
class AdminResource(resource.Resource):
    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/admin", b"")
        admin_msg = "Authentication required. Use default credentials or send auth token."
        return Message(payload=admin_msg.encode())

    async def render_post(self, request):
        log_request(request.remote.hostinfo, "POST", "/admin", request.payload)
        try:
            payload_data = request.payload.decode()
            if "user=admin" in payload_data and "pass=admin" in payload_data:
                return Message(code=Code.CHANGED, payload=b"Login successful. Welcome, Administrator.")
            else:
                return Message(code=Code.UNAUTHORIZED, payload=b"Authentication failed.")
        except:
            return Message(code=Code.BAD_REQUEST, payload=b"Invalid request format")

class ConfigResource(resource.Resource):
    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/config", b"")
        # Configuration avec "secrets" exposés
        config = {
            "device_id": "IoT-GW-" + ''.join(random.choices('0123456789ABCDEF', k=8)),
            "api_key": "sk_" + ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=24)),
            "mqtt_server": "broker.example.com",
            "mqtt_user": "iot_device",
            "mqtt_pass": "iot_secret_123",
            "update_interval": 60,
            "debug_mode": True
        }
        return Message(payload=json.dumps(config).encode())

    async def render_put(self, request):
        log_request(request.remote.hostinfo, "PUT", "/config", request.payload)
        # Simuler une vulnérabilité d'injection
        try:
            payload_data = request.payload.decode()
            print(f"[CONFIG] Configuration update attempt: {payload_data}")
            if ";" in payload_data or "&" in payload_data:
                print("[ALERT] Possible command injection attempt!")
            return Message(code=Code.CHANGED, payload=b"Configuration updated")
        except:
            return Message(code=Code.BAD_REQUEST, payload=b"Invalid configuration")

class ControlResource(resource.Resource):
    async def render_post(self, request):
        log_request(request.remote.hostinfo, "POST", "/control", request.payload)
        try:
            command = request.payload.decode()
            print(f"[CONTROL] Received command: {command}")

            # Simuler des actions en fonction de la commande
            if "reboot" in command.lower():
                return Message(code=Code.CHANGED, payload=b"System reboot scheduled in 5 seconds")
            elif "shutdown" in command.lower():
                return Message(code=Code.CHANGED, payload=b"System shutdown scheduled in 5 seconds")
            elif "reset" in command.lower():
                return Message(code=Code.CHANGED, payload=b"Factory reset initiated")
            else:
                return Message(code=Code.CHANGED, payload=b"Command acknowledged")
        except:
            return Message(code=Code.BAD_REQUEST, payload=b"Invalid command format")

class DiscoveryResource(resource.Resource):
    async def render_get(self, request):
        log_request(request.remote.hostinfo, "GET", "/.well-known/core", b"")
        links = '</temperature>;rt="sensor";if="core.s",</camera>;rt="video";if="core.p",'
        links += '</debug>;rt="core.d",</firmware>;rt="core.f",</admin>;rt="core.a",</config>;rt="core.c",'
        links += '</control>;rt="core.ctrl"'
        return Message(payload=links.encode('utf8'))

async def main():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("# CoAP Honeypot Logs - Started on " + datetime.datetime.now().isoformat() + "\n")
    else:
        with open(LOG_FILE, "a") as f:
            f.write("\n# --- Honeypot restarted on " + datetime.datetime.now().isoformat() + " ---\n\n")


    root = resource.Site()
    root.add_resource(['temperature'], TemperatureResource())
    root.add_resource(['camera'], CameraResource())
    root.add_resource(['debug'], DebugResource())
    root.add_resource(['firmware'], FirmwareResource())

    root.add_resource(['admin'], AdminResource())
    root.add_resource(['config'], ConfigResource())
    root.add_resource(['control'], ControlResource())

    root.add_resource(['.well-known', 'core'], DiscoveryResource())

    await Context.create_server_context(root, bind=('::', 5683))

    print("CoAP honeypot server started with endpoints:")
    print("- /temperature: Simulated temperature sensor")
    print("- /camera: Simulated security camera")
    print("- /debug: System debugging information (with fake leaks)")
    print("- /firmware: Firmware update endpoint (with simulated vulnerabilities)")
    print("- /admin: Administrative interface (with weak authentication)")
    print("- /config: System configuration (with exposed credentials)")
    print("- /control: Control interface (with command processing)")
    print("- /.well-known/core: Resource discovery")
    print(f"Logging all requests to {LOG_FILE}")

    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Honeypot server stopped by user")
