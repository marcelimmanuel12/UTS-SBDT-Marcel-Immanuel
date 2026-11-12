#!/usr/bin/env bash
set -euo pipefail
printf 'PRIMARY (hasil false):\n'
docker compose exec -T postgres-primary psql -U sbdt -d sbdt -tAc 'SELECT pg_is_in_recovery();'
printf 'REPLICA (hasil true):\n'
docker compose exec -T postgres-replica psql -U sbdt -d sbdt -tAc 'SELECT pg_is_in_recovery();'
printf 'STREAM STATUS (ideal streaming):\n'
docker compose exec -T postgres-primary psql -U sbdt -d sbdt -c 'SELECT application_name, state, sync_state FROM pg_stat_replication;'
