#!/bin/sh
set -eu
# Untuk laboratorium lokal; produksi batasi alamat client di pg_hba.conf.
printf '%s\n' 'host replication replicator 0.0.0.0/0 scram-sha-256' >> "$PGDATA/pg_hba.conf"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v rep_pass="$REPLICATION_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD %L', :'rep_pass') \gexec
SQL
