import asyncio
import random
import base64
import datetime
import os
from aiocoap import *
from aiocoap import resource

LOG_FILE = "coap_honeypot.log"

def log_request(remote, method, path, payload):
    with open(LOG_FILE, "a") as f:
        log_line = f"{datetime.datetime.now()}, {remote}, {method}, {path}, {payload.decode(errors='ignore')}\n"
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
        fake_image = base64.b64encode(b"This is a fake camera image")
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
        debug_info = "System OK. Temp=%.2f. Logs clear." % random.uniform(22, 30)
        return Message(payload=debug_info.encode())

class FirmwareResource(resource.Resource):
    async def render_post(self, request):
        log_request(request.remote.hostinfo, "POST", "/firmware", request.payload)
        if len(request.payload) > 100:
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=b"Firmware upload failed (buffer overflow?)")
        return Message(code=Code.CHANGED, payload=b"Firmware uploaded successfully")

async def main():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    root = resource.Site()
    root.add_resource(['temperature'], TemperatureResource())
    root.add_resource(['camera'], CameraResource())
    root.add_resource(['debug'], DebugResource())
    root.add_resource(['firmware'], FirmwareResource())

    await Context.create_server_context(root)
    print("CoAP honeypot server started with endpoints: /temperature, /camera, /debug, /firmware")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
