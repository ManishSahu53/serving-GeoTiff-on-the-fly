import multiprocessing

bind = "0.0.0.0:4000"
# workers = multiprocessing.cpu_count() * 2 + 1
# worker_class = "gevent"
timeout = 120
graceful_timeout = 120


SEARCH_API = 'http://40.117.155.223:5000/api/v1/search'
CDNURL = 'https://dvqjhul01jnkw.cloudfront.net'

BUCKET = 'satellite-dataset-prod'
AWS_REGION = 'us-east-2'
