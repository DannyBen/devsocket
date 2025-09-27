import asyncio
from typing import Dict, Set
from aiohttp import web, WSMsgType

# channel -> set of WebSocketResponse
subscribers: Dict[str, Set[web.WebSocketResponse]] = {}
lock = asyncio.Lock()

async def broadcast(channel: str, payload):
    async with lock:
        conns = list(subscribers.get(channel, set()))
    if not conns:
        return 0

    dead = []
    sent = 0
    for ws in conns:
        try:
            # Send text; if dict/list, aiohttp will json-dump for send_json
            if isinstance(payload, (dict, list)):
                await ws.send_json({"channel": channel, "data": payload})
            else:
                await ws.send_str(payload if isinstance(payload, str) else str(payload))
            sent += 1
        except Exception:
            dead.append(ws)

    if dead:
        async with lock:
            for ws in dead:
                for ch, set_ in list(subscribers.items()):
                    if ws in set_:
                        set_.discard(ws)
                        if not set_:
                            subscribers.pop(ch, None)
    return sent

async def ws_handler(request: web.Request):
    channel = request.match_info["channel"]
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    async with lock:
        subscribers.setdefault(channel, set()).add(ws)

    try:
        async for msg in ws:
            # We don't expect client→server messages; just ignore pings/text.
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
    if ctype.startswith("application/json"):
        data = await request.json()
        payload = {"channel": channel, "data": data}
        delivered = await broadcast(channel, payload)  # send unified json envelope
    else:
        text = (await request.read()).decode("utf-8", errors="replace")
        payload = {"channel": channel, "data": text}
        delivered = await broadcast(channel, payload)
    return web.json_response({"ok": True, "delivered": delivered})

def create_app():
    app = web.Application()
    app.add_routes([
        web.get("/ws/{channel}", ws_handler),
        web.post("/publish/{channel}", publish_handler),
    ])
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=3000)
