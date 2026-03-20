
redis_cache: redis-server config/redis_cache.conf
redis_queue: redis-server config/redis_queue.conf


web: bench serve  --port 8002


socketio: /home/vineelreddykamireddy/.config/nvm/versions/node/v24.13.0/bin/node apps/frappe/socketio.js


watch: bench watch


schedule: bench schedule

worker:  bench worker 1>> logs/worker.log 2>> logs/worker.error.log

