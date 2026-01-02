import asyncio
import websockets

clients = set()
document_text = ""

async def handler(websocket):
    global document_text
    clients.add(websocket)

    await websocket.send(document_text)

    try:
        async for message in websocket:
            document_text = message
            for client in clients:
                if client != websocket:
                    await client.send(document_text)
    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())
