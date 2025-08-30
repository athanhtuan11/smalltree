bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
loglevel = "info"
pidfile = "/home/smalltree/smalltree/unicorn.pid"
errorlog = "/home/smalltree/smalltree/unicorn_error.log"
accesslog = "/home/smalltree/smalltree/unicorn_access.log"
