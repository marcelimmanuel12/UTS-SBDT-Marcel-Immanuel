#!/bin/sh
set -eu
: "${PGDATA:=/var/lib/postgresql/data/pgdata}"
: "${REPLICATION_PASSWORD:?REPLICATION_PASSWORD harus diisi}"
mkdir -p "$PGDATA"
chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"
export PGPASSWORD="$REPLICATION_PASSWORD"
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  echo "Menunggu primary untuk basebackup..."
  until pg_isready -h postgres-primary -p 5432 -U sbdt >/dev/null 2>&1; do sleep 2; done
  # pg_basebackup -R menulis standby.signal dan primary_conninfo.
  su-exec postgres pg_basebackup -h postgres-primary -p 5432 -U replicator \
    -D "$PGDATA" -F p -X stream -R -w
fi
exec su-exec postgres postgres -D "$PGDATA" -c hot_standby=on
