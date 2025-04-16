import asyncio
import random
import base64
from aiocoap import *
from aiocoap import resource

class TemperatureResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.temperature = 20.0
        asyncio.get_event_loop().create_task(self.update_temperature())

    async def render_get(self, request):
        payload = f'{self.temperature:.2f} °C'.encode('utf8')
        return Message(payload=payload)

    async def update_temperature(self):
        protocol = await Context.create_client_context()
        while True:
            self.temperature = 20 + random.uniform(-3, 8)  # pour augmenter la proba > 25
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
    def __init__(self):
        super().__init__()

    async def render_get(self, request):
        fake_image = base64.b64encode(b"This is a fake camera image")
        print("[Camera] Sending image...")
        return Message(payload=fake_image)

    async def render_post(self, request):
        print(f"[Camera] Received POST: {request.payload.decode()}")
        ack = b"Camera stream started (simulated)"
        return Message(code=Code.CHANGED, payload=ack)

async def main():
    root = resource.Site()
    root.add_resource(['temperature'], TemperatureResource())
    root.add_resource(['camera'], CameraResource())

    await Context.create_server_context(root)
    print("CoAP honeypot server started with /temperature and /camera")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
