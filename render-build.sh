#!/usr/bin/env bash
set -euo pipefail

echo "==> Starting render build script"

# Move to backend directory where requirements.txt and app code live
cd src/backend

echo "==> Upgrading pip and installing requirements"
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "No requirements.txt found in src/backend; skipping pip install"
fi

# Optional: run database migrations if you use Alembic and DB is available
# echo "==> Running migrations"
# if command -v alembic >/dev/null 2>&1; then
#   alembic upgrade head
# fi

echo "==> Build script finished"
