import asyncio
import websockets
import json
import sys

async def listen_to_scanner():
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a scanner_id as a command-line argument.")
        print("Usage: python scanner_client.py <your_scanner_id>")
        return

    scanner_id = sys.argv[1]
    uri = f"ws://localhost:8000/ws/scanner/alerts/{scanner_id}"

    print(f"Connecting to scanner at: {uri}")

    async with websockets.connect(uri) as websocket:
        print(f"✅ Connected to scanner {scanner_id}!")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get('type') == 'scanner_alert':
                    print("\n" + "="*40)
                    print(f"🚨 SCANNER ALERT 🚨")
                    print(f"  Symbol:   {data['symbol']}")
                    print(f"  Signal:   {data['signal']}")
                    print(f"  Price:    {data['price']:.2f}")
                    print(f"  Strategy: {data['strategy_name']}")
                    print(f"  Time:     {data['timestamp']}")
                    print("="*40)
                else:
                    print(f"ℹ️ Server message: {data.get('message')}")

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, attempting to reconnect...")
                break

if __name__ == "__main__":
    asyncio.run(listen_to_scanner())
