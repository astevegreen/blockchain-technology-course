@echo off
rem Stop Course Labs (Windows): double-click it. It stops every lab and the control page, and keeps
rem your work. --dry-run is accepted for the tests; Stop opens nothing.
setlocal
rem "call docker" runs docker.exe as usual and lets the tests put a fake docker.cmd first on PATH.
where docker >nul 2>&1 || (echo Docker isn't installed, so no labs are running.& exit /b 0)
call docker info >nul 2>&1 || (echo Docker isn't running, so no labs are running.& exit /b 0)
echo Stopping the course labs. Your work is kept...
call docker exec course-launcher wget -q -T 900 -O /dev/null --post-data= http://127.0.0.1:8470/api/shutdown >nul 2>&1
call docker rm -f course-launcher >nul 2>&1
echo The course labs are stopped. Double-click Start Course Labs to carry on later.
if /i not "%~1"=="--dry-run" ping -n 4 127.0.0.1 >nul
exit /b 0
