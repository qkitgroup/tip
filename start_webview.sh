#!/bin/sh
# start webview with gunicorn webserver with 4 threads, listen locally on port 8000 (0.0.0.0:8000)
gunicorn web.webview:server -w 4 -b :8000
