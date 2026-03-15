#!/bin/bash
# Force install dependencies if Azure skipped them
pip install --no-cache-dir -r requirements.txt
gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 600
