#!/bin/bash
set -e

echo "Current directory:"
pwd

echo "Directory contents:"
ls -la

echo "Python path:"
echo $PYTHONPATH

echo "Python version:"
python --version

echo "Installed packages:"
pip list

echo "Attempting to import the app:"
python -c "from src.app import create_app; app = create_app()"

echo "Starting Gunicorn"
exec gunicorn --bind 0.0.0.0:5000 --log-level debug wsgi:app