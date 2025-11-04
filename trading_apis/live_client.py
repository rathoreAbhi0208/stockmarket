# simple_client.py
import asyncio
import websockets
import json

async def listen_to_signals():
    uri = "ws://localhost:8000/ws/live_strategy_3min/NIFTY"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'signal_update':
                    print(f"\n📊 {data['symbol']}: {data['final_signal']}")
                    
                elif data['type'] == 'alert':
                    print(f"\n🚨 {data['signal']} ALERT!")
                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, reconnecting...")
                break

# Run
asyncio.run(listen_to_signals())