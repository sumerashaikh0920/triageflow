#!/bin/sh
# Runs once, the first time the Postgres data volume is initialised
# (mounted into /docker-entrypoint-initdb.d by the root docker-compose.yml).
# Creates the separate database used by the ML service.
#
# If you change ML_POSTGRES_DB after the first boot, this will NOT re-run:
# create the database by hand, or reset with `docker compose down -v`.
set -e

ML_DB="${ML_POSTGRES_DB:-triageflow_ml}"

psql -v ON_ERROR_STOP=1 -v ml_db="$ML_DB" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
SELECT format('CREATE DATABASE %I', :'ml_db')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'ml_db') \gexec
EOSQL

echo "ML database '$ML_DB' is ready."
