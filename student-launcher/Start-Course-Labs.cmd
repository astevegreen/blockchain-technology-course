@echo off
rem Start Course Labs (Windows): double-click it. It starts the control page that runs the labs,
rem then opens it. --dry-run prints what it would open or start instead.
setlocal
rem "call docker" runs docker.exe as usual and lets the tests put a fake docker.cmd first on PATH.
set "IMAGE=ghcr.io/astevegreen/course-labs:launcher-stable"
if defined COURSE_LABS_IMAGE set "IMAGE=%COURSE_LABS_IMAGE%"
set "GUIDE=https://astevegreen.github.io/blockchain-technology-course/run-labs.html#install-docker"
set "PAGE=http://127.0.0.1:8470/"
set "DRY="
if /i "%~1"=="--dry-run" set "DRY=1"
where docker >nul 2>&1 || (call :open "%GUIDE%" & echo Docker Desktop isn't installed. The guide that just opened shows how to install it.& goto :fail)
call docker info >nul 2>&1 && goto :ready
echo Starting Docker Desktop. This can take a minute...
set "DD=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not exist "%DD%" set "DD=%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
if defined DRY (echo would: start "%DD%") else (start "" "%DD%")
for /l %%i in (1,1,40) do (
  call docker info >nul 2>&1 && goto :ready
  if defined DRY goto :nodocker
  ping -n 4 127.0.0.1 >nul
)
:nodocker
echo Docker didn't start. Open Docker Desktop yourself, wait until it says it is running, then try again.
goto :fail
:ready
echo Getting the latest course labs. The first time takes a few minutes...
call docker pull "%IMAGE%" >nul 2>&1 || call docker image inspect "%IMAGE%" >nul 2>&1 || (echo Couldn't download the course labs. Check your internet connection, then try again.& goto :fail)
call docker rm -f course-launcher >nul 2>&1
call docker run -d --name course-launcher --restart unless-stopped -e LAUNCHER_IMAGE="%IMAGE%" -v /var/run/docker.sock:/var/run/docker.sock -v course-launcher-state:/state -p 127.0.0.1:8470:8470 "%IMAGE%" >nul 2>&1 || (echo The course labs didn't start. Restart Docker Desktop, then try again.& goto :fail)
for /l %%i in (1,1,60) do (
  call docker exec course-launcher wget -q -O /dev/null %PAGE%api/health >nul 2>&1 && goto :up
  if not defined DRY ping -n 2 127.0.0.1 >nul
)
:up
call :open "%PAGE%"
echo The course labs page is open in your browser at %PAGE%
exit /b 0
:fail
if not defined DRY pause
exit /b 1
:open
if defined DRY (echo would: open %~1) else (start "" "%~1")
exit /b 0
