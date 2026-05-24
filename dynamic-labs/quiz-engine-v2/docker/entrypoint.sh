#!/bin/sh
set -eu

flask --app app:create_app init-db
exec "$@"
