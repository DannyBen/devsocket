# DevSocket - HTTP → WebSocket Server for Development

A minimal bridge that lets you **publish messages over HTTP** and **consume them over WebSockets**.

⚠️ **Important**: this project is intended for **development and testing only**.

* No authentication or TLS included.
* Single-process, in-memory only (no persistence, no multi-instance fan-out).

---

## Features

* Simple: one file server (`app.py`) + static demo page.
* Publish messages as **plain text** or **JSON** over HTTP.
* Subscribe to a **channel** via WebSocket and receive those messages live.
* Available as:
  * **Python app** (using aiohttp)
  * **Docker container**

---

## Endpoints

### WebSocket

* `GET /ws/{channel}`
  Subscribe to messages on a channel.
  Example: `ws://localhost:3000/ws/test`

Messages delivered as JSON envelope:

```json
{
  "channel": "test",
  "data": "hello world"
}
```

### HTTP publish

* `POST /publish/{channel}`
  Send a message to a channel.

  * If `Content-Type: application/json` → payload is parsed JSON.
  * Otherwise → raw body is used as a string.

Response:

```json
{ "ok": true, "delivered": 1 }
```

---

## Run (Python)

```bash
git clone https://github.com/dannyben/devsocket.git
cd devsocket
python -m pip install -r requirements.txt
python app.py
```

Server runs at [http://localhost:3000](http://localhost:3000).

Open the demo UI: [http://localhost:3000](http://localhost:3000)

---

## Run (Docker)

You can run the [pre-built Docker image](https://hub.docker.com/r/dannyben/devsocket)
directly from Docker Hub:

```bash
docker run --rm -p 3000:3000 dannyben/devsocket
```

Open [http://localhost:3000](http://localhost:3000) to use the demo page.

### Run with Docker Compose

Here’s a minimal `docker-compose.yml`:

```yaml
services:
  devsocket:
    image: dannyben/devsocket
    ports:
      - "3000:3000"
```

Run it with:

```bash
docker compose up
```

---

## Quick Testing

### 1. Simple `<script>` subscriber

Paste into your browser console or a blank HTML page:

```html
<script>
  const ws = new WebSocket("ws://localhost:3000/ws/test");
  ws.onmessage = (e) => console.log("got:", JSON.parse(e.data));
</script>
```

Now you’ll see messages logged when published.

---

### 2. Publish plain text with curl

```bash
curl -X POST http://localhost:3000/publish/test \
  --data 'hello world'
```

---

### 3. Publish JSON with curl

```bash
curl -X POST http://localhost:3000/publish/test \
  -H 'Content-Type: application/json' \
  -d '{"msg":"hi","n":1}'
```

---

## Demo Page

The server also serves a simple demo UI at `/` (static HTML).
Features:

* Connect to a channel.
* Send plain text or JSON.
* Live WebSocket message log.

Open: [http://localhost:3000](http://localhost:3000)

---

## License

MIT — feel free to fork and hack for your local testing needs.
