# HLF Reset And Startup

This document describes the optional fresh-start procedure for the HLF
regression suite.

This is not the default entry path. The default case is to run against
the existing live environment without wiping it first.

Goal:

- make the HLF environment feel like a fresh lab boot
- preserve built Docker images
- discard HLF runtime state, claims, generated student material,
  containers, and volumes

Important:

- this is optional and used only when fresh-start coverage is requested
- preserve images
- do not preserve container writable state
- do not preserve named volumes
- do not preserve `hlf/runtime`
- preserve `hlf/managed_runtime`, which contains checked-in bootstrap
  templates and topology files required for startup

## Default Entry Path

The default regression run should not wipe the environment.

If the environment is already live, the normal starting point is:

```bash
./lab-manager.sh start hlf
./lab-manager.sh status hlf
```

Use the fresh-start procedure below only when explicitly requested or
when the current HLF environment is not trustworthy.

## Optional Fresh-Start Reset

Run these steps from the repo root.

### 1. Stop the HLF lab

```bash
./lab-manager.sh stop hlf || true
```

### 2. Tear down the HLF compose project and volumes

```bash
cd hlf
docker compose down -v --remove-orphans || true
cd ..
```

### 3. Clear generated HLF runtime state

```bash
rm -rf hlf/runtime/*
```

This preserves the checked-in source tree and built images while wiping
the generated network runtime, claims, progress state, and container
state. Do not delete `hlf/managed_runtime`; it is part of the source
tree for this lab, not disposable runtime state.

## Fresh-Start Startup

### 1. Start the HLF lab again

```bash
./lab-manager.sh start hlf
```

### 2. Confirm expected services are up

```bash
./lab-manager.sh status hlf
```

## Minimum Post-Boot Smoke

Before deeper regression checks, verify these routes respond through the
shared router:

- `/labs/hlf/`
- `/labs/hlf/claim`
- `/labs/hlf/instructor/`
- `/labs/hlf/explorer/`
- `/labs/hlf/peer/org5/`

The automated suite should prefer Python `requests` for these checks.
