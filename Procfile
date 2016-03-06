web: gunicorn --access-logfile - --log-file - --workers 4 --max-requests 1200 --bind 0.0.0.0:${PORT-8000} --pythonpath apps app.wsgi
