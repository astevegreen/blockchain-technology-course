# Byzantine Generals Simulation

This folder contains a self-contained Flask and Flask-SocketIO app for a single-player self-study walkthrough of Byzantine fault tolerance and consensus failure.

The app supports:

- UUID-based session reconnects via a `uuid` value stored in the URL
- student-designed self-service rooms (pick room size and malicious node count)
- bot-generated peers that fill the remaining seats
- broadcast, tally, and debrief phases
- a staged Vis.js debrief graph for stepping through the message flow

## Project Layout

```text
app/
  app.py                 Flask factory, routes, health check
  config.py              Environment-driven configuration
  state/game_state.py    In-memory room, player, and bot logic
  sockets/events.py      Socket.IO event handlers
  templates/
    index.html           Student UI
  static/
    css/style.css
    js/student.js
run.py                   Local development entrypoint
requirements.txt         Python dependencies
Dockerfile               Container image definition
.dockerignore            Build context exclusions
```

## Important Deployment Note

This app intentionally stores all state in Python memory:

- room assignments
- per-player inboxes
- final votes
- debrief data

That means it is designed for short-lived self-study sessions, not a horizontally scaled production deployment.

Because of that:

- run exactly one application process
- run exactly one Gunicorn worker
- do not load-balance multiple replicas of the app unless you first move state into a shared backend such as Redis or a database

The included Dockerfile enforces a single Gunicorn worker for this reason.

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

Supported variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | No | `byzantine-generals-secret` | Flask session signing key |
| `FLASK_DEBUG` | No | `0` | Enables Flask debug mode for local development |
| `HOST` | No | `0.0.0.0` | Host binding for `run.py` |
| `PORT` | No | `5000` | Port for local or container runs |

## Running Locally Without Docker

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create an environment file:

```bash
cp .env.example .env
```

4. Start the app:

```bash
python3 run.py
```

5. Open the student view: `http://localhost:5000/`

The student view writes a `uuid` query parameter into the browser URL on first load. That URL is the student identity for refreshes and reconnects, so students should keep or reopen the same link if they want to resume their session.

From the lobby the student picks room size and malicious node count, then starts immediately with bots filling the remaining seats. After the round finishes, the student reveals the debrief and uses the staged graph controls: stage stepping, fit-to-view, node/edge inspection.

Health check endpoint:

- `http://localhost:5000/healthz`

## Docker Usage

### Build the Image

From this folder:

```bash
docker build -t bgp-game:latest .
```

### Run the Container

The simplest local run publishes port `5000` directly:

```bash
docker run --rm \
  --name bgp-game \
  --env-file .env \
  -p 5000:5000 \
  bgp-game:latest
```

Then open `http://localhost:5000/`.

### How the Container Starts

The container runs:

```bash
gunicorn --worker-class eventlet --workers 1 --timeout 0 --bind 0.0.0.0:5000 run:app
```

Why this matters:

- `eventlet` is required for Socket.IO long-lived connections and WebSocket upgrades
- `--workers 1` is required because the app uses in-memory state
- `--timeout 0` avoids Gunicorn killing healthy long-lived Socket.IO requests
- the container logs access and error output to stdout/stderr so it behaves well in Docker
- committed `app/static/vendor/` bundles provide `socket.io-client@4.7.5` and `vis-network@9.1.9` so Socket.IO and the debrief graph work without external CDNs

## Running Behind Nginx Reverse Proxy

Nginx must be configured to support:

- HTTP/1.1 upstream proxying
- WebSocket upgrade headers
- long read timeouts for live sessions
- forwarded host and scheme headers

The app already uses `ProxyFix`, so it understands:

- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `X-Forwarded-Host`
- `X-Forwarded-Prefix`

### Recommended Option: Root Path Proxy

This is the simplest deployment model. Nginx owns the public host, and proxies the entire site to the app container.

Example Nginx config:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream bgp_game {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name bgp.example.com;

    location / {
        proxy_pass http://bgp_game;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

### Alternate Option: Subpath Proxy

If Nginx serves multiple apps on the same domain, you can mount this app under a path prefix such as `/bgp-game/`.

This app has been updated to behave correctly behind a forwarded prefix:

- template URLs use Flask `url_for(...)`
- Flask honors `X-Forwarded-Prefix`
- Socket.IO clients derive their connection path from `request.script_root`

Example Nginx config for a subpath deployment:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream bgp_game {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name example.com;

    location /bgp-game/ {
        proxy_pass http://bgp_game/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /bgp-game;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

Important details for subpath mode:

- keep the trailing slash in `location /bgp-game/`
- keep the trailing slash in `proxy_pass http://bgp_game/;`
- set `X-Forwarded-Prefix /bgp-game`
- do not strip the WebSocket upgrade headers

## Common Troubleshooting

### The page loads but live updates do not work

Usually this means the reverse proxy is missing WebSocket upgrade headers. Check:

- `proxy_http_version 1.1;`
- `proxy_set_header Upgrade $http_upgrade;`
- `proxy_set_header Connection $connection_upgrade;`

### Static files or Socket.IO break under a subpath

Usually this means the reverse proxy is not sending `X-Forwarded-Prefix`, or the path rewrite does not preserve the trailing slash behavior expected by Nginx.

### Students lose their rooms after restart

This is expected if the app process restarts. All room state is in memory and is reset when the Python process exits.

### Can I increase Gunicorn workers?

Not with the current architecture. More workers would split players and rooms across separate Python processes and break the simulation state.
