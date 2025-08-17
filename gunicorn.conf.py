# Gunicorn configuration for smalltree Website
# File: gunicorn.conf.py

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/smalltree/gunicorn_access.log"
errorlog = "/var/log/smalltree/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "smalltree_gunicorn"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/smalltree/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# Worker timeout and memory limits
worker_tmp_dir = "/dev/shm"
worker_class = "sync"

# Graceful timeout
graceful_timeout = 30

# SSL (uncomment if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'FLASK_DEBUG=0',
]

# Custom application-specific settings
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
