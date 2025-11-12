# test_ws.py
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/ws/test"
    
    try:
        print("Connecting...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            while True:
                message = await websocket.recv()
                print(f"Received: {message}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test())