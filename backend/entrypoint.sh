#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PYCODE'
import time
import sys
from sqlalchemy import create_engine, text
from app.config import settings

for attempt in range(30):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database is ready.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"  attempt {attempt + 1}/30: database not ready ({exc}), retrying...")
        time.sleep(2)
print("Database never became ready.", file=sys.stderr)
sys.exit(1)
PYCODE

echo "Running Alembic migrations..."
alembic upgrade head

if [ "$SEED_ON_STARTUP" = "true" ]; then
    echo "Seeding demo data..."
    python -m app.seed
fi

echo "Starting server..."
exec "$@"
