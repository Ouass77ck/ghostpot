import asyncio
from aiocoap import *

async def simulate_client():
    context = await Context.create_client_context()

    while True:
        temp_req = Message(code=GET, uri='coap://localhost/temperature')
        response = await context.request(temp_req).response
        print(f"[Client] Temp: {response.payload.decode()}")

        cam_req = Message(code=GET, uri='coap://localhost/camera')
        cam_resp = await context.request(cam_req).response
        print(f"[Client] Camera image (simulated): {cam_resp.payload[:10]}...")

        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(simulate_client())
