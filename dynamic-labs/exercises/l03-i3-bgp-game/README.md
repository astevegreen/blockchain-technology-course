# Byzantine Generals Simulation

This folder contains a self-contained Flask and Flask-SocketIO classroom app for simulating Byzantine fault tolerance and consensus failure.

The app supports:

- student UUID-based reconnects via a `uuid` value stored in the URL
- instructor authentication via the shared instructor portal in normal lab deployments
- collaborative rooms and self-service rooms
- student-designed self-service rooms
- student-controlled self-service debrief reveal with the full interactive graph explorer
- bot-generated peers for self-service play
- instructor-triggered AFK takeover so a stalled room can continue
- broadcast, tally, and debrief phases
- a staged Vis.js debrief graph for classroom walkthroughs

## Project Layout

```text
app/
  app.py                 Flask factory, routes, auth, health check
  config.py              Environment-driven configuration
  state/game_state.py    In-memory room, player, queue, and bot logic
  sockets/events.py      Socket.IO event handlers
  templates/
    index.html           Student UI
    instructor.html      Instructor dashboard
  static/
    css/style.css
    js/student.js
    js/instructor.js
run.py                   Local development entrypoint
requirements.txt         Python dependencies
Dockerfile               Container image definition
.dockerignore            Build context exclusions
```

## Important Deployment Note

This app intentionally stores all state in Python memory:

- lobby queue
- room assignments
- per-player inboxes
- final votes
- debrief data

That means it is designed for a short-lived classroom session, not a horizontally scaled production deployment.

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
| `HLF_INSTRUCTOR_COOKIE_SECRET` | No | empty | Preferred shared-cookie verification secret |
| `HLF_WEB_SECRET_KEY` | No | `hlf_lab_secret` in local dev | Shared-cookie verification fallback |
| `INSTRUCTOR_AUTH_MODE` | No | `shared` | `shared`, `standalone`, or `disabled` |
| `INSTRUCTOR_AUTH_SECRET` | Standalone only | empty | Cookie signing secret in standalone mode |
| `INSTRUCTOR_PASSWORD` | Standalone only | empty | Standalone `/instructor/login` password |
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

5. Open the two views:

- student view: `http://localhost:5000/`
- instructor view: `http://localhost:5000/instructor`

For a direct local run without the shared router, enable standalone instructor auth first:

```bash
INSTRUCTOR_AUTH_MODE=standalone \
INSTRUCTOR_AUTH_SECRET=dev-secret \
INSTRUCTOR_PASSWORD=admin \
python3 run.py
```

The student view writes a `uuid` query parameter into the browser URL on first load. That URL is the student identity for refreshes and reconnects, so students should keep or reopen the same link if they want to resume their session.

Collaborative Mode remains instructor-driven. Self-Service Mode can now be launched entirely from the student view: the student switches to Self-Service Mode, chooses room size and malicious node count, and the room starts immediately with bots filling the remaining seats.
After the self-service round finishes, the student can reveal the debrief themselves and use the same staged graph controls the instructor uses: stage stepping, zoom, pan, fit-to-view, and node/edge inspection.

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

Then open:

- `http://localhost:5000/`
- `http://localhost:5000/instructor`

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
- the Docker build also installs `socket.io-client@4.7.5` and `vis-network@9.1.9` in a Node build stage, then copies both browser bundles into `app/static/vendor/` so Socket.IO and the debrief graph work without external CDNs

## Running Behind Nginx Reverse Proxy

Nginx must be configured to support:

- HTTP/1.1 upstream proxying
- WebSocket upgrade headers
- long read timeouts for live classroom sessions
- forwarded host and scheme headers

The app already uses `ProxyFix`, so it understands:

- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `X-Forwarded-Host`
- `X-Forwarded-Prefix`

### Recommended Option: Root Path Proxy

This is the simplest deployment model. Nginx owns the public host, and proxies the entire site to the app container.

Example container run:

```bash
docker run -d \
  --name bgp-game \
  --restart unless-stopped \
  --env-file .env \
  -p 5000:5000 \
  bgp-game:latest
```

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

With that setup:

- students use `https://bgp.example.com/`
- instructors use `https://bgp.example.com/instructor`

In the full dynamic-labs deployment behind the shared router, the public instructor URL is `/exercises/bgp/instructor` and authentication is handled centrally at `/instructor/`.

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

With that setup:

- students use `https://example.com/bgp-game/`
- instructors use `https://example.com/bgp-game/instructor`

## Running Nginx and the App on the Same Docker Network

If both Nginx and this app run as containers, place them on the same Docker network and point Nginx at the container name instead of `127.0.0.1`.

Example app container:

```bash
docker network create bgp-net

docker run -d \
  --name bgp-game \
  --network bgp-net \
  --env-file .env \
  bgp-game:latest
```

Then in Nginx:

```nginx
upstream bgp_game {
    server bgp-game:5000;
}
```

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

## Suggested Production-Like Setup

For a classroom or workshop deployment, the practical stack is:

1. one container for this app
2. one Nginx reverse proxy in front of it
3. TLS termination at Nginx
4. one app worker only
5. a plan to restart between classroom sessions rather than during one

## Summary

For the simplest reliable deployment:

1. build the Docker image
2. run one container with `.env`
3. put Nginx in front of it
4. pass WebSocket headers through
5. keep the app on a single worker because all state is in memory
