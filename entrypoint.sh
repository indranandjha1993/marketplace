#!/bin/sh
set -e  # Exit on any error

# Wait for database to be ready
echo "Waiting for database at $DB_HOST:$DB_PORT..."
attempts=30
until python -c "import MySQLdb; MySQLdb.connect(host='$DB_HOST', user='$DB_USER', passwd='$DB_PASSWORD', db='$DB_NAME', port=int('$DB_PORT'))" 2>/dev/null; do
    if [ $attempts -eq 0 ]; then
        echo "Error: Database connection failed after maximum attempts"
        exit 1
    fi
    echo "Database unavailable, retrying in 5 seconds... ($attempts attempts left)"
    sleep 5
    attempts=$((attempts-1))
done
echo "Database connection established"

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate --noinput --verbosity 2

# Collect static files (if needed)
if [ "$COLLECT_STATIC" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Skipping static file collection (COLLECT_STATIC not set to true)"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 90 marketplace.wsgi:application
