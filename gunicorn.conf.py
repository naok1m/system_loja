import os

bind = '0.0.0.0:' + os.environ.get('PORT', '10000')
workers = 1       # free tier tem 512MB; 2 workers = OOM kills
timeout = 120     # cold start após hibernação pode demorar
keepalive = 5
preload_app = True  # carrega o app uma vez, antes de fazer fork dos workers
