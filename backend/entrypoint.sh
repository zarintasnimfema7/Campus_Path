#!/bin/sh
set -eu

# exec makes Uvicorn PID 1 so it receives termination signals directly.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
