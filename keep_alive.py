"""
Azure Free Tier Cold Start 방지를 위한 Keep-Alive 스크립트
GitHub Actions나 외부 서비스에서 주기적으로 호출
"""

import requests
import time
from datetime import datetime

def ping_webapp(url):
    """웹앱에 핑을 보내서 활성 상태 유지"""
    try:
        response = requests.get(f"{url}/api/code", timeout=30)
        print(f"[{datetime.now()}] Ping successful: {response.status_code}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Ping failed: {e}")
        return False

if __name__ == "__main__":
    # 웹앱 URL을 환경변수나 설정에서 가져오기
    WEBAPP_URL = "https://your-app.azurewebsites.net"
    
    # 15분마다 핑 (Azure Free Tier는 20분 후 종료)
    while True:
        ping_webapp(WEBAPP_URL)
        time.sleep(15 * 60)  # 15분 대기