import asyncio
import websockets
import json
import sqlite3
from datetime import datetime
import atexit
from aiohttp import web
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

WEBSOCKET_URL = "wss://jetstream1.us-east.bsky.network/subscribe"
DB_NAME = "image_stats.db"
WEB_PORT = 8080

# Global connection and cursor
conn = None
cursor = None

# Set to store connected websocket clients
connected_clients = set()

def init_db():
    global conn, cursor
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS counters
        (id INTEGER PRIMARY KEY, images_with_alt INTEGER, images_without_alt INTEGER)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS start_time
        (id INTEGER PRIMARY KEY, start_datetime TEXT)
    ''')

    cursor.execute('INSERT OR IGNORE INTO counters (id, images_with_alt, images_without_alt) VALUES (1, 0, 0)')

    cursor.execute('INSERT OR IGNORE INTO start_time (id, start_datetime) VALUES (1, ?)', (datetime.now().isoformat(),))

    conn.commit()

def close_db():
    if conn:
        conn.close()

atexit.register(close_db)

async def update_counters(with_alt, without_alt):
    cursor.execute('''
        UPDATE counters
        SET images_with_alt = images_with_alt + ?,
            images_without_alt = images_without_alt + ?
        WHERE id = 1
    ''', (with_alt, without_alt))
    conn.commit()

    current_values = get_current_values()
    message = json.dumps({
        "images_with_alt": current_values[0],
        "images_without_alt": current_values[1]
    })
    await broadcast(message)

async def broadcast(message):
    logger.info(f"Broadcasting message to {len(connected_clients)} clients: {message}")
    for client in connected_clients.copy():  # Use a copy to avoid modification during iteration
        try:
            await client.send_str(message)
            logger.info(f"Message sent to client successfully")
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            connected_clients.remove(client)

def get_current_values():
    cursor.execute('SELECT images_with_alt, images_without_alt FROM counters WHERE id = 1')
    return cursor.fetchone()

def reset_start_time():
    cursor.execute('UPDATE start_time SET start_datetime = ? WHERE id = 1', (datetime.now().isoformat(),))
    conn.commit()

def get_start_time():
    cursor.execute('SELECT start_datetime FROM start_time WHERE id = 1')
    return cursor.fetchone()[0]

async def process_event(event):
    if event.get('kind') != 'commit':
        return

    commit = event.get('commit', {})
    if (commit.get('operation') != 'create'):
        return
    if (commit.get('collection') != 'app.bsky.feed.post'):
        return

    record = commit.get('record', {})
    if 'embed' not in record or record.get('embed').get('$type') != 'app.bsky.embed.images':
        return

    images_with_alt = 0
    images_without_alt = 0
    for image in record.get('embed').get('images'):
        if image.get('alt'):
            images_with_alt += 1
        else:
            images_without_alt += 1

    await update_counters(images_with_alt, images_without_alt)

async def listen_to_websocket():
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        print(f"Connected to {WEBSOCKET_URL}")

        while True:
            try:
                message = await websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                return

            try:
                event = json.loads(message)
            except json.JSONDecodeError:
                print(f"Received non-JSON message: {message}")
                continue

            await process_event(event)

async def handle_websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    logger.info(f"New WebSocket connection established")
    connected_clients.add(ws)

    try:
        current_values = get_current_values()
        start_time = get_start_time()
        initial_message = json.dumps({
            "images_with_alt": current_values[0],
            "images_without_alt": current_values[1],
            "start_time": start_time
        })
        await ws.send_str(initial_message)
        logger.info(f"Sent initial message: {initial_message}")

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket connection closed with exception {ws.exception()}')
    finally:
        connected_clients.remove(ws)
        logger.info(f"WebSocket connection closed")

    return ws

async def index(request):
    with open('index.html', 'r') as f:
        content = f.read()
    return web.Response(text=content, content_type='text/html')

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/ws', handle_websocket)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', WEB_PORT)
    await site.start()
    print(f"Web server started on http://localhost:{WEB_PORT}")

async def main():
    init_db()
    await start_web_server()

    while True:
        try:
            await listen_to_websocket()
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
