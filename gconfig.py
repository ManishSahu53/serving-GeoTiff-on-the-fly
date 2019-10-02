import multiprocessing

bind = "0.0.0.0:4000"
# workers = multiprocessing.cpu_count() * 2 + 1
# worker_class = "gevent"
timeout = 120
graceful_timeout = 120

LAMBDA_VALUE_API = 'https://zsgz8nr1fh.execute-api.us-east-2.amazonaws.com/dev/api/v1/value?'
SEARCH_API = 'http://18.215.245.62:5000/api/v1/search'
CDNURL = 'https://dvqjhul01jnkw.cloudfront.net'

BUCKET = 'satellite-dataset-prod'
AWS_REGION = 'us-east-2'
AWS_ACCESS_KEY_ID = 'AKIAJ3NMSUWXPHTIOXSA'
AWS_SECRET_ACCESS_KEY = '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'