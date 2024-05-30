echo "Waiting for DB to be reachable..."
until psql --host=$DATABASE_HOST --port=$DATABASE_PORT --username=$DATABASE_USER --dbname=$DATABASE_NAME -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Start the main process
echo "Starting server..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000