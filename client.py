import asyncio
from aiocoap import *
import random

async def get_temperature():
    print("[Client] Requesting temperature...")
    protocol = await Context.create_client_context()
    request = Message(code=GET, uri='coap://192.168.XX.XX/temperature') #put the ip add of the honeypot
    try:
        response = await protocol.request(request).response
        print(f"[Client] Temperature: {response.payload.decode()}")
    except Exception as e:
        print(f"[Client] Failed to get temperature: {e}")

async def get_camera_image():
    print("[Client] Requesting camera image...")
    protocol = await Context.create_client_context()
    request = Message(code=GET, uri='coap://192.168.2.66/camera')
    try:
        response = await protocol.request(request).response
        print(f"[Client] Camera image (base64): {response.payload.decode()}")
    except Exception as e:
        print(f"[Client] Failed to get camera image: {e}")

async def start_camera_stream():
    print("[Client] Sending POST to /camera...")
    protocol = await Context.create_client_context()
    request = Message(code=POST, uri='coap://192.168.2.66/camera', payload=b'stream start')
    try:
        response = await protocol.request(request).response
        print(f"[Client] Camera response: {response.payload.decode()}")
    except Exception as e:
        print(f"[Client] Failed to post to camera: {e}")

async def get_debug_info():
    print("[Client] Requesting debug info...")
    protocol = await Context.create_client_context()
    request = Message(code=GET, uri='coap://192.168.2.66/debug')
    try:
        response = await protocol.request(request).response
        print(f"[Client] Debug info: {response.payload.decode()}")
    except Exception as e:
        print(f"[Client] Failed to get debug info: {e}")

async def upload_firmware(fake_size=50):
    print(f"[Client] Uploading firmware ({fake_size} bytes)...")
    fake_payload = b'\x00' * fake_size
    protocol = await Context.create_client_context()
    request = Message(code=POST, uri='coap://192.168.2.66/firmware', payload=fake_payload)
    try:
        response = await protocol.request(request).response
        print(f"[Client] Firmware upload response: {response.payload.decode()}")
    except Exception as e:
        print(f"[Client] Firmware upload failed: {e}")

async def main():
    await get_temperature()
    await get_camera_image()
    await start_camera_stream()
    await get_debug_info()
    await upload_firmware(fake_size=50)  #success
    await upload_firmware(fake_size=150) #should simulate buffer overflow

if __name__ == "__main__":
    asyncio.run(main())
