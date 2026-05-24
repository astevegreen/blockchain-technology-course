# Bitcoin Reset And Startup

This document describes the optional fresh-start procedure for the
Bitcoin regression suite.

This is not the default entry path. The default case is to run against
the existing live environment without wiping it first.

Goal:

- make the environment feel like a fresh VM run
- preserve built Docker images
- discard runtime state, claims, volumes, generated credentials, and
  containers

Important:

- this is optional and used only when fresh-start coverage is requested
- preserve images
- do not preserve container writable state
- do not preserve named volumes
- do not preserve lane-service runtime state

## Default Entry Path

The default regression run should not wipe the environment.

Use the current environment as-is when:

- the relevant shared services are already running
- the Bitcoin lab is already running or can be started without teardown
- there is no evidence of stale or contaminated state

If the environment is already live, the normal starting point is:

```bash
./lab-manager.sh start bitcoin
./lab-manager.sh status router
./lab-manager.sh status instructor-auth-service
./lab-manager.sh status lane-service
./lab-manager.sh status bitcoin
```

Use the fresh-start procedure below only when explicitly requested or
when the current environment is not trustworthy.

## Optional Fresh-Start Reset

Run these steps from the repo root.

### 1. Stop managed services

```bash
./lab-manager.sh stop all || true
```

### 2. Tear down compose projects and volumes

Run `docker compose down -v --remove-orphans` in each managed project.

Recommended order:

```bash
cd router && docker compose down -v --remove-orphans || true
cd ../course-site && docker compose down -v --remove-orphans || true
cd ../instructor_auth_service && docker compose down -v --remove-orphans || true
cd ../lane-service && docker compose down -v --remove-orphans || true
cd ../bitcoin && docker compose down -v --remove-orphans || true
cd ../consensus && docker compose down -v --remove-orphans || true
cd ../cryptography && docker compose down -v --remove-orphans || true
cd ../p2p_trust && docker compose down -v --remove-orphans || true
cd ../ethereum_lab && docker compose down -v --remove-orphans || true
cd ../exercises && docker compose down -v --remove-orphans || true
cd ../quiz-engine-v2 && docker compose down -v --remove-orphans || true
cd ../hlf && docker compose down -v --remove-orphans || true
cd ..
```

Why this is necessary:

- `lane-service` owns spawned Bitcoin student lanes and should be brought
  down so its stop hooks can clean them up
- `bitcoin` owns the instructor and mempool containers plus the
  `bitcoin-instructor-data` volume
- other shared services can leave state behind that makes the run look
  like a restart instead of a first deployment

### 3. Clear bind-mounted runtime state

```bash
rm -rf lane-service/runtime/*
rm -rf .runtime
rm -f .lab-manager.env
```

This wipes generated runtime credentials, deployment mode state, and the
lane-service claim or progress state that survives outside Docker
volumes.

### 4. Confirm images were preserved

Do not run image-prune commands as part of the reset.

The reset may recreate containers, but it should reuse already-built
images.

## Fresh-Start Startup

### 1. Recreate shared runtime state

```bash
./lab-manager.sh deploy --mode instructor --no-tls --max-student-capacity 2
```

This regenerates `.runtime/`, recreates required networks, and starts
shared infrastructure.

### 2. Start the Bitcoin lab

```bash
./lab-manager.sh start bitcoin
```

### 3. Confirm expected services are up

```bash
./lab-manager.sh status router
./lab-manager.sh status instructor-auth-service
./lab-manager.sh status lane-service
./lab-manager.sh status bitcoin
```

### 4. Record the generated instructor credentials

```bash
cat .runtime/instructor-credentials.txt
```

## Minimum Post-Boot Smoke

Before deeper regression checks, verify these routes respond through the
shared router:

- `/`
- `/instructor/`
- `/labs/bitcoin/`
- `/labs/bitcoin/mempool/`
- `/labs/bitcoin/btc-explorer/`
- `/labs/bitcoin/admin`
- `/labs/bitcoin/instructor/`

The automated suite should prefer Python `requests` for these checks.
