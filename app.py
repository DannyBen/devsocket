import asyncio
from typing import Dict, Set
from aiohttp import web, WSMsgType
import pathlib

# channel -> set of WebSocketResponse
subscribers: Dict[str, Set[web.WebSocketResponse]] = {}
lock = asyncio.Lock()


async def remove_dead_connections(dead: list):
    async with lock:
        for ws in dead:
            for channel, connections in list(subscribers.items()):
                if ws in connections:
                    connections.discard(ws)
                    if not connections:
                        subscribers.pop(channel, None)


async def broadcast(channel: str, message):
    async with lock:
        connections = list(subscribers.get(channel, set()))
    if not connections:
        return 0

    dead = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)

    if dead:
        await remove_dead_connections(dead)
    return len(connections) - len(dead)


async def ws_handler(request: web.Request):
    channel = request.match_info["channel"]
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    async with lock:
        subscribers.setdefault(channel, set()).add(ws)

    try:
        async for msg in ws:
            if msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break
    finally:
        async with lock:
            if channel in subscribers:
                subscribers[channel].discard(ws)
                if not subscribers[channel]:
                    subscribers.pop(channel, None)
    return ws


async def publish_handler(request: web.Request):
    channel = request.match_info["channel"]
    ctype = request.headers.get("content-type", "")
    if ctype and ctype.startswith("application/json"):
        data = await request.json()
    else:
        data = (await request.read()).decode("utf-8", errors="replace")
    message = {"channel": channel, "data": data}
    delivered = await broadcast(channel, message)
    return web.json_response({"ok": True, "delivered": delivered})


def create_app():
    app = web.Application()
    app.add_routes([
        web.get("/ws/{channel}", ws_handler),
        web.post("/publish/{channel}", publish_handler),
        web.get("/", lambda request: web.FileResponse("demo.html")),
    ])

    return app


def main():
    web.run_app(create_app(), host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
