# The Insider

`The Insider` is a small-group social deduction game built with Flask and Flask-SocketIO. One hidden Insider tries to survive or guess the secret word, while everyone else uses clues and voting to expose them.

This app supports:

- Open games, optional private games, and QR/link-based joining
- Human and agent players, with the instructor controlling whether bots backfill empty seats
- Sequential or simultaneous clue reveal
- Live timers, reconnect grace periods, and instructor moderation

## Requirements

- Python 3.11+
- `pip`
- Optional: Docker
- Optional for production: a reverse proxy such as Nginx or Caddy

## Installation

### Local Python setup

From the app directory:

```bash
cd dynamic-labs/exercises/l03-i3-trust-game
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run locally

For simple local development:

```bash
python app.py
```

The app will start on:

- Student view: `http://localhost:5000/`
- Instructor dashboard: `http://localhost:5000/instructor`

For a production-like local run:

```bash
gunicorn -k eventlet -w 1 --timeout 0 --bind 0.0.0.0:5000 app:app
```

## Docker

Build and run:

```bash
cd dynamic-labs/exercises/l03-i3-trust-game
docker build -t insider-game .
docker run --rm -p 5000:5000 \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e INSTRUCTOR_AUTH_MODE=standalone \
  -e INSTRUCTOR_AUTH_SECRET="$(openssl rand -hex 32)" \
  -e INSTRUCTOR_PASSWORD="<choose-a-password>" \
  insider-game
```

The two secrets are generated fresh on each run, so every run gets its own.
Replace `<choose-a-password>` with the password you will type on the instructor
login page; there is no built-in password to fall back on.

The included `Dockerfile` already:

- Installs the Python dependencies
- Vendors the Socket.IO browser client
- Runs Gunicorn with Eventlet

## Configuration

### Environment variables

The app supports these environment variables:

- `SECRET_KEY`
  - Flask session secret. Required: the app refuses to start without it
  - In a full deployment, `./lab-manager.sh deploy` generates a different value for each deployment
    (as `TRUST_GAME_SECRET_KEY`) into `dynamic-labs/.runtime/runtime-secrets.env`
    (owner-readable only, git-ignored, not in the student download)
  - Running the container on its own: pass your own value with `-e SECRET_KEY=...`
- `HLF_INSTRUCTOR_COOKIE_SECRET`
  - Preferred shared-cookie verification secret in shared mode
- `HLF_WEB_SECRET_KEY`
  - Shared-cookie verification fallback in shared mode
- `INSTRUCTOR_AUTH_MODE`
  - `shared` by default in the full dynamic-labs deployment
  - Use `standalone` for direct local runs without the shared router
- `INSTRUCTOR_AUTH_SECRET`
  - Cookie signing secret in standalone mode
- `INSTRUCTOR_PASSWORD`
  - Password for the standalone `/instructor/login` page
  - Required in standalone mode

### Instructor dashboard settings

Most gameplay behavior is configured live from `/instructor`.

Available controls:

- `Game is online for students`
  - Turns the student game on or off during instruction
- `Backfill empty seats with bots`
  - When on, any player can start the round and bots fill the remaining seats up to the recommended group size
- `Allow private rooms`
  - When on, students can create or join private rooms by code; turn off to force everyone into open rooms
- `Old game retention`
  - How long finished rooms stay visible in the instructor dashboard after everyone leaves
- `Reveal mode`
  - `simultaneous`: all clues are committed, then revealed together
  - `random`: clues are revealed one at a time in random order
- `Disconnect grace seconds`
  - Time a disconnected player has to reclaim their seat before removal
- `Action timeout seconds`
  - Time allowed for clue submission and voting before timeout elimination
- `Context shown to students`
  - Short scenario text displayed in the student UI
- `Optional custom secret words`
  - One word per line
  - Replaces the default word pool for future rounds

## Routes

- `/`
  - Student view
- `/instructor`
  - Instructor dashboard
  - Protected by the shared `hlf_instructor` cookie in normal deployments
- `/room/<ROOM_ID>/qr.png`
  - QR code image for joining a room by link

When deployed behind a reverse proxy prefix, these routes move under that prefix. For example, with a prefix of `/games/insider`, the student view becomes `/games/insider/`.

## Roles and Gameplay Modes

### Roles

- `Regular player`
  - Receives the secret word for the current round
  - Gives a one-word clue
  - Votes for the most suspicious player
- `Insider`
  - Does not receive the secret word
  - Tries to blend in
  - Can guess the word at any time
  - Gets a final guess if voted out
- `Agent`
  - Optional AI-controlled participant
  - Can fill empty seats
  - Can act as either a regular player or the Insider

### Room modes

- `Open game`
  - Any player can join the next available open room
- `Private game`
  - Room is created privately and joined by room code or link
- `Linked room`
  - A direct room URL joins a specific room

### Reveal modes

- `Simultaneous reveal`
  - Everyone commits a clue first
  - All clues become visible together after commit completes
- `Sequential reveal`
  - Clues are revealed one player at a time
  - In this mode, each new clue must be different from earlier revealed clues

## Rules Summary

### Goal

- The group is trying to identify and eliminate the Insider.
- The Insider is trying to survive, or guess the secret word correctly before the group can stop them.

### Round structure

Each game contains multiple rounds.

For each round:

1. A new secret word is selected.
2. Regular players see the word. The Insider does not.
3. Players submit one-word clues.
4. The room votes for the most suspicious player.
5. If the Insider is caught, they get one final guess at the secret word.

### Important rules

- The Insider stays the same across the whole game.
- The secret word changes each round.
- Duplicate clues are not allowed.
- In sequential reveal mode, a player must wait for their turn and submit a different clue from prior revealed clues.
- A tied vote eliminates nobody and the game continues to another round.
- If a non-Insider is eliminated, that player is removed and the game continues unless the Insider has now survived to three active players.
- Players who disconnect or time out are removed but remain visible in the roster with their status.

### Win conditions

- `Group wins`
  - The Insider is eliminated and misses the final guess
  - The Insider disconnects and is removed
  - The Insider times out and is removed
  - The Insider guesses incorrectly at any point
- `Insider wins`
  - The Insider guesses the secret word correctly at any point
  - The Insider survives until only three active players remain

## Joining and reconnecting

- Open rooms can be joined from the lobby or by direct room link
- Private rooms are joined by room code or direct room link
- Each player gets a room/player URL that can be used to reclaim their seat after refresh or temporary disconnect
- Seats are preserved server-side, not by browser storage

## Deployment Behind a Reverse Proxy

### Important architecture note

This app keeps room state in memory inside a single Python process.

That means:

- Run a single application instance unless you add shared state yourself
- Keep Gunicorn at one worker for the current architecture
- Make sure your reverse proxy forwards WebSocket traffic correctly

The included Docker image already uses:

```bash
gunicorn -k eventlet -w 1 --timeout 0 --bind 0.0.0.0:5000 app:app
```

### Root deployment

If you are serving the app at the site root, a standard reverse proxy works:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

### Deploy under a subdirectory

This app can also run under a URL prefix such as `/games/insider/`.

For that deployment style:

- The reverse proxy should strip the prefix before forwarding requests to Flask
- The reverse proxy should send `X-Forwarded-Prefix` with that prefix
- WebSocket upgrade headers still need to be forwarded
- The app should still run as a single instance / single worker because room state is in memory

The app now uses Flask's forwarded prefix support to generate:

- student links
- QR join links
- static asset URLs
- Socket.IO transport paths

### Nginx subdirectory example

Example Nginx site config for `/games/insider/`:

```nginx
server {
    listen 80;
    server_name example.com;

    location /games/insider/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /games/insider;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

Important detail: the trailing slash on `proxy_pass` strips `/games/insider/` before the request reaches Flask.

### Reverse proxy checklist

- Forward normal HTTP traffic to the Flask/Gunicorn container
- Forward WebSocket upgrade headers
- Use a long enough read timeout for live rooms
- Terminate TLS at the proxy if you need HTTPS
- Keep all requests for a session on the same app instance
- If using a subdirectory, forward `X-Forwarded-Prefix`
- If using a subdirectory, strip the prefix before proxying upstream

### Caddy root example

```caddy
example.com {
    reverse_proxy 127.0.0.1:5000
}
```

Caddy handles WebSocket upgrades automatically in standard reverse proxy mode.

### Caddy subdirectory example

For a subdirectory deployment at `/games/insider/`:

```caddy
example.com {
    handle_path /games/insider/* {
        header_up X-Forwarded-Prefix /games/insider
        reverse_proxy 127.0.0.1:5000
    }
}
```

`handle_path` strips the matched prefix before forwarding the request upstream.

## Instructor access

In the full dynamic-labs deployment, instructors log in once at `/instructor/` and then access this dashboard at `/exercises/insider/instructor`.

For a direct local run without the shared router, enable standalone mode first:

```bash
SECRET_KEY="$(openssl rand -hex 32)" \
INSTRUCTOR_AUTH_MODE=standalone \
INSTRUCTOR_AUTH_SECRET="$(openssl rand -hex 32)" \
INSTRUCTOR_PASSWORD="<choose-a-password>" \
python app.py
```

## Notes

- This repository version is designed for small classroom or workshop deployments.
- If you want horizontal scaling, persistent rooms, or durable session state, you will need to move room state out of process memory.
