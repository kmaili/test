# Non logging stuff
bind = "0.0.0.0:5000"
workers = 4
threads = 4

# Access log - records incoming HTTP requests
accesslog = "/app/logs/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/app/logs/gunicorn.error.log"
# Whether to send Django output to the error log
capture_output = True
# How verbose the Gunicorn error logs should be
loglevel = "info"

chdir = "/app"
