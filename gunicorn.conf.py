# Gunicorn configuration for Azure Web App optimization
import multiprocessing
import os

# 서버 소켓
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"

# Worker 프로세스
# Azure free tier의 메모리 제한을 고려하여 worker 수를 1개로 제한
workers = 1  # Free tier에서는 1개 worker가 최적
worker_class = "sync"
worker_connections = 500  # Free tier에 맞게 연결 수 제한

# 메모리 최적화
max_requests = 500  # 메모리 누수 방지를 위해 낮게 설정
max_requests_jitter = 25
preload_app = True

# 타임아웃
timeout = 60
keepalive = 2
graceful_timeout = 30

# 로깅
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 성능 튜닝
worker_tmp_dir = "/dev/shm"  # 메모리 기반 임시 디렉토리 사용 (가능한 경우)