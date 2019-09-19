import multiprocessing

bind = "0.0.0.0:4000"
# workers = multiprocessing.cpu_count() * 2 + 1
# worker_class = "gevent"
timeout = 120
graceful_timeout = 120


SEARCH_API = 'localhost:5000/api/v1/search'
CDNURL = 'https://d2l0edunqm5wgb.cloudfront.net'

BUCKET = 'test-satellite-dataset'
AWS_REGION = 'eu-central-1'
