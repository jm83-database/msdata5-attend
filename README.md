# 출석 관리 시스템 사용 가이드

## 목차
1. [시스템 개요](#시스템-개요)
2. [주요 기능](#주요-기능)
3. [프로젝트 구조](#프로젝트-구조)
4. [시작하기](#시작하기)
    - [프로젝트 설치](#프로젝트-설치)
    - [Azure Cosmos DB 설정](#azure-cosmos-db-설정)
    - [환경 변수 설정](#환경-변수-설정)
    - [학생 명단 준비](#학생-명단-준비)
    - [서버 실행](#서버-실행)
5. [사용 방법](#사용-방법)
    - [선생님 모드](#선생님-모드)
    - [학생 모드](#학생-모드)
6. [학생 관리](#학생-관리)
    - [학생 삭제](#학생-삭제)
    - [학생 복구](#학생-복구)
    - [엑셀 파일 동기화](#엑셀-파일-동기화)
7. [최신 업데이트](#최신-업데이트)
8. [문제 해결](#문제-해결)
9. [커스터마이징](#커스터마이징)

## 시스템 개요

출석 관리 시스템은 교육 환경에서 학생들의 출석을 효율적으로 관리하기 위한 웹 기반 애플리케이션입니다. 이 시스템은 자동 생성되는 출석 코드와 학생별 비밀번호를 통해 출석 확인의 정확성과 신뢰성을 높이고, 실시간으로 출석 현황을 모니터링할 수 있게 해줍니다.

**업데이트 (2026년 2월)**: 이제 Azure Cosmos DB를 사용하여 모든 데이터가 클라우드에 안전하게 저장됩니다. 더 이상 Azure App Service idle 상태에서 데이터가 손실되지 않습니다!

## 주요 기능

- **클라우드 데이터 저장**: Azure Cosmos DB를 사용한 안전한 클라우드 저장소 (로컬 JSON 폴백 지원)
- **엑셀 통합**: 기존 엑셀 파일에서 학생 명단 자동 추출 및 동기화
- **출석 코드 관리**: 5분 유효 기간의 출석 코드 자동 생성 및 관리
- **개인 비밀번호**: 학생별 고유 비밀번호로 출석 인증 보안 강화
- **실시간 모니터링**: 총원 대비 실시간 출석률 시각화 및 학생별 상태 확인
- **데이터 내보내기**: 출석 데이터 CSV 파일로 내보내기
- **학생 관리**: 학생 삭제 및 복구 기능 (영구 저장됨)
- **모바일 지원**: 다양한 기기에서 최적화된 사용자 경험 제공
- **커스텀 favicon 지원**: 브라우저 탭에 사용자 지정 아이콘 표시
- **환경변수 설정**: 보안을 위해 교사 비밀번호가 환경변수에서 관리됨

## 프로젝트 구조

```
msai10_attend/
├── logs/                      # 로그 폴더 (로컬 개발용)
│   └── deleted_students.json  # 삭제된 학생 정보 기록 (폴백용)
├── static/                    # 정적 파일 폴더
│   ├── css/                   # CSS 파일 폴더
│   │   └── tailwind.min.css   # Tailwind CSS 파일
│   ├── images/                # 스크린샷 및 이미지 파일 폴더
│   ├── js/                    # JavaScript 파일 폴더
│   │   ├── libs/              # 외부 라이브러리 폴더
│   │   └── main.js            # 메인 JavaScript 파일
│   └── profile.png            # Favicon 이미지
├── templates/                 # HTML 템플릿 폴더
│   └── index.html             # 메인 페이지 HTML
├── add-passwords-to-students.py  # 학생 비밀번호 생성 스크립트
├── app.py                     # 메인 애플리케이션 서버 (Flask)
├── cosmos_service.py          # Azure Cosmos DB 데이터 접근 계층 ⭐ NEW
├── excel-to-students.py       # 엑셀에서 학생 정보 추출 스크립트
├── gunicorn.conf.py           # Gunicorn 서버 설정 파일 (Azure 최적화)
├── keep_alive.py              # Azure Web App idle 방지 스크립트
├── .env.example               # 환경변수 설정 파일 예시 ⭐ NEW
├── .gitignore                 # Git 무시 파일
├── MS AI School 10기 Teams 계정.xlsx  # 예시 엑셀 파일
├── README.md                  # 프로젝트 설명서
├── requirements.txt           # 의존성 패키지 목록
├── startup.txt                # 서버 시작 관련 정보
├── students.json              # 학생 데이터 파일 (폴백용)
└── update_students.py         # 학생 정보 업데이트 스크립트
```

위 구조는 프로젝트의 전체적인 파일 및 폴더 구성을 보여줍니다. 각 파일과 폴더의 역할을 이해하면 프로젝트를 더 쉽게 관리하고 수정할 수 있습니다.

## 시작하기

### 프로젝트 설치

```bash
# 필요한 패키지 설치
pip install -r requirements.txt
```

### Azure Cosmos DB 설정

이 시스템은 이제 Azure Cosmos DB를 사용합니다. 프로덕션 환경에서 먼저 다음을 수행하세요:

#### 1. Azure Portal에서 Cosmos DB 계정 생성
1. [Azure Portal](https://portal.azure.com)에 접속
2. "Create a resource" → "Azure Cosmos DB" 클릭
3. 다음 정보로 계정 생성:
   - **Account Name**: `attendance-cosmos` (전역적으로 고유해야 함)
   - **API**: `Core (SQL)` 선택 ⚠️ 중요
   - **Location**: East Asia (또는 가장 가까운 지역)
   - **Capacity Mode**: `Provisioned throughput`
   - **Throughput**: `400 RU/s`

#### 2. 데이터베이스 및 컨테이너 생성
1. 배포 완료 후 "Go to resource" 클릭
2. "Data Explorer" → "New Database" 클릭
   - **Database ID**: `attendance_db`
3. "New Container" 클릭
   - **Database ID**: `attendance_db`
   - **Container ID**: `attendance_data`
   - **Partition key**: `/cohort_id` ⚠️ 중요 (코호트별 격리)
   - **Throughput**: `400 RU/s`

#### 3. 연결 정보 수집
1. "Keys" 탭에서 다음 정보 복사:
   - **URI**: `COSMOS_ENDPOINT`로 사용
   - **Primary Key**: `COSMOS_KEY`로 사용

### 환경 변수 설정

#### 로컬 개발 환경
1. `.env.example` 복사하여 `.env` 파일 생성:
```bash
cp .env.example .env
```

2. `.env` 파일에 Cosmos DB 정보 입력:
```bash
COSMOS_ENDPOINT=https://your-endpoint.documents.azure.com:443/
COSMOS_KEY=your-primary-key-here
COSMOS_DB=attendance_db
COSMOS_CONTAINER=attendance_data
COHORT_ID=AIXX
TEACHER_PASSWORD=sample
```

#### Azure App Service (프로덕션)
Azure Portal에서 각 앱에 대해 **Configuration** → **Application settings**에서 추가:

| 설정 | 값 | 비고 |
|------|-----|------|
| `COSMOS_ENDPOINT` | https://your-endpoint.documents.azure.com:443/ | 공통 |
| `COSMOS_KEY` | (Primary Key) | 공통 |
| `COSMOS_DB` | attendance_db | 공통 |
| `COSMOS_CONTAINER` | attendance_data | 공통 |
| `COHORT_ID` | `AI10` / `AI9` / `DT3` / `DT4` | **프로젝트별 다름** |
| `TEACHER_PASSWORD` | (보안 암호) | 공통 |

> 💡 **팁**: 새 코호트를 추가할 때는 코드 변경 없이 `COHORT_ID` 환경변수만 변경하면 됩니다!

### 학생 명단 준비

1. **엑셀 파일 준비**
   - 기본 파일명: `MS AI School 6기 Teams 계정.xlsx`
   - 학생 이름이 포함된 열이 있어야 함 ('이름', 'Name', '성명', '학생명' 등의 열 인식)

2. **학생 목록 추출**
   ```bash
   python excel-to-students.py
   ```

3. **학생 비밀번호 생성**
   ```bash
   python add-passwords-to-students.py
   ```

`students.json` 파일은 다음과 같은 형식의 JSON 배열을 포함합니다:
```json
[
    {
        "id": 1,
        "name": "홍길동",
        "present": false,
        "code": "",
        "timestamp": null,
        "password": "1234"
    },
    // 다른 학생 정보
]
```

### 서버 실행

#### 개발 환경
```bash
# Flask 개발 서버 (개발용)
FLASK_ENV=development python app.py
```

#### 프로덕션 환경 (Azure Web App)
```bash
# Gunicorn 서버 사용 (권장)
gunicorn -c gunicorn.conf.py app:app

# 또는 기본 실행 (자동으로 Waitress/Flask 서버 선택)
python app.py
```

서버는 기본적으로 개발 환경에서는 `http://localhost:5000/`, 프로덕션에서는 `http://localhost:8000/`에서 실행됩니다.

## Azure Web App 배포 순서

이 섹션은 변경된 코드를 Azure Web App에 배포하는 단계별 가이드입니다.

### 1단계: Azure Cosmos DB 설정 (최초 1회만)
```bash
# Azure Portal에서 수동으로 진행
# README.md의 "Azure Cosmos DB 설정" 섹션 참고

1. Cosmos DB 계정 생성
   - 계정명: attendance-cosmos
   - API: Core (SQL) ⚠️ 중요
   - 위치: East Asia

2. 데이터베이스 및 컨테이너 생성
   - 데이터베이스: attendance_db
   - 컨테이너: attendance_data
   - Partition key: /cohort_id ⚠️ 중요

3. 연결 정보 복사 (Keys 탭)
   - URI → COSMOS_ENDPOINT
   - Primary Key → COSMOS_KEY
```

### 2단계: 로컬 테스트 (선택)
```bash
cd D:\dev\github\msai10-attend

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (또는 Cosmos DB 정보 없이 JSON 폴백으로 테스트)
cp .env.example .env

# 로컬 서버 실행
python app.py

# http://localhost:5000에서 테스트
```

### 3단계: Git에 커밋
```bash
cd D:\dev\github\msai10-attend

# 변경된 파일 확인
git status

# 스테이지에 추가
git add .

# 커밋
git commit -m "feat: Azure Cosmos DB 통합, 환경변수 보안 강화"

# 원격 저장소에 푸시
git push origin main
```

### 4단계: Azure Portal에서 환경변수 설정 ⭐ 중요
```
Azure Portal → App Services → [msai10-attend] → Configuration

"Application settings" 섹션에서:

+ New application setting 클릭하여 추가:

COSMOS_ENDPOINT     → https://attendance-cosmos.documents.azure.com:443/
COSMOS_KEY          → (Primary Key 값)
COSMOS_DB           → attendance_db
COSMOS_CONTAINER    → attendance_data
COHORT_ID           → AI10
TEACHER_PASSWORD    → (보안 암호)

💡 팁: 다른 코호트(AI9, DT3, DT4)는 COHORT_ID만 다르게 설정

저장 버튼 클릭 → 앱 자동 재시작
```

### 5단계: 배포
```bash
# Option 1: Azure CLI로 수동 배포 (권장)
az webapp up --name msai10-attend --resource-group [리소스그룹명]

# Option 2: Git 자동 배포 (이미 설정되었으면)
git push origin main  # 자동 배포됨
```

### 6단계: 배포 확인
```bash
# App Service 로그 확인
az webapp log tail --name msai10-attend --resource-group [리소스그룹명]

# 또는 Azure Portal
# App Services → [msai10-attend] → Log stream에서 실시간 확인

# 웹 브라우저에서 확인
https://msai10-attend.azurewebsites.net
```

### 7단계: 기능 테스트
```
웹 브라우저에서 다음을 확인하세요:

1. 학생 목록 로드 확인
2. 출석 코드 생성 (teacher 또는 환경변수 TEACHER_PASSWORD 입력)
3. 학생 출석 확인
4. 삭제된 학생이 Cosmos DB에 저장되는지 확인
5. CSV 다운로드 테스트
```

### ⚠️ 주의사항

| 항목 | 주의 |
|------|------|
| **Cosmos DB 생성** | 최초 1회만 필요, 이후 모든 코호트가 같은 DB 사용 |
| **COHORT_ID** | AI10, AI9, DT3, DT4 각각 다르게 설정 필요 |
| **환경변수** | 코드에 하드코딩되면 안 됨, 반드시 Azure Portal에서 설정 |
| **TEACHER_PASSWORD** | 프로덕션에서 'teacher'는 절대 금지! 보안 암호로 변경 |
| **테스트** | 배포 전 로컬에서 JSON 폴백으로 기본 동작 확인 권장 |

## 사용 방법

### 선생님 모드

![출석 관리 시스템 메인 화면](./static/images/teacher_screen.png)

선생님 모드는 시스템에 접속했을 때 기본 모드로, 다음 기능을 제공합니다:

#### 빠른 이동 메뉴
화면 오른쪽 하단에 고정된 메뉴 버튼들이 있어 편리하게 이동할 수 있습니다:
- **상단으로 이동**: 페이지 상단으로 바로 이동
- **학생 목록으로 이동**: 학생 명단 테이블로 바로 이동
- **하단으로 이동**: 페이지 하단으로 바로 이동

### 고정 헤더 기능

스크롤을 내려도 항상 화면 상단에 고정되어 보이는 헤더 영역은 다음 요소를 포함합니다:
- 시스템 타이틀과 모드 정보
- 시간과 모드 전환 버튼
- 현재 출석 코드와 유효 시간
- 실시간 출석률 현황
- 학생 목록 제목

모달창이 열리면 일시적으로 고정 헤더가 숨겨졌다가, 모달이 닫히면 다시 표시됩니다.

#### 출석 코드 관리

- **출석 코드 생성**: '새 코드 생성' 버튼으로 6자리 무작위 코드 생성
- **코드 유효 시간**: 생성 후 5분 동안 유효 (자동 만료)
- **상태 표시**: 코드의 유효/만료 상태를 색상으로 표시 (유효: 파란색, 만료: 빨간색)
- **타이머**: 코드 만료까지 남은 시간 카운트다운

#### 출석 현황 모니터링

- **실시간 출석률**: X/Y명 (Z%) 형식과 프로그레스 바로 시각화
- **학생 목록 테이블**: 이름, 출석 상태, 확인 시간, 관리 기능(삭제)
- **학생 체크박스**: 선택한 여러 학생을 일괄 삭제할 수 있는 기능

### 모달 카드 기능

모듬 카드는 다음 특성을 가집니다:
- 화면 중앙에 표시되어 사용성 향상
- 배경 투명도 개선으로 가시성 향상 
- 모달 열리면 고정 헤더 자동 숨김
- 표준화된 디자인으로 일관성 제공

모달에는 다음 기능이 포함됩니다:
- 선생님 인증 모달
- 학생 삭제 확인 모달
- 학생 일괄 삭제 확인 모달
- 학생 복구 확인 모달
- 삭제된 학생 목록 모달

### 관리 기능

- **출석부 초기화**: 모든 학생의 출석 상태 재설정
- **출석부 CSV 다운로드**: 출석 기록 CSV 파일로 내보내기
- **학생 비밀번호 다운로드**: 학생 이름과 비밀번호 목록 CSV 다운로드
- **삭제된 학생 목록**: 삭제된 학생 조회 및 복구

> ⚠️ **주의 사항**: 수업이 끝나고 새로운 수업이 시작되기 전에는 반드시 출석부 CSV 다운로드를 먼저 완료한 후 출석부 초기화를 해야 합니다. 초기화하지 않으면 출석 기록이 계속 유지됩니다.

> 관리 기능을 사용하려면 선생님 비밀번호(기본값: 'teacher')를 입력해야 합니다.

### 학생 모드

![학생 모드 화면](./static/images/student_screen.png)

학생 모드로 전환하여 다음과 같은 방식으로 출석을 확인할 수 있습니다:

1. 화면 우측 상단의 "학생 모드로 전환" 버튼 클릭
2. 다음 정보 입력:
   - **이름**: 본인 이름
   - **출석 코드**: 선생님이 제공한 유효한 코드
   - **개인 비밀번호**: 개인에게 부여된 비밀번호
3. "출석 확인" 버튼 클릭

출석 코드가 유효하고 이름과 비밀번호가 일치하면 성공 메시지가 표시됩니다. ![학생 만료 화면](./static/images/expired_student_screen.png)

## 학생 관리

### 학생 삭제
![삭제 화면](./static/images/delete_screen.png)

1. 선생님 모드의 학생 목록에서 삭제할 학생의 '삭제' 버튼 클릭
2. 확인 팝업에서 선생님 비밀번호 입력
3. '삭제' 버튼 클릭

> 삭제된 학생 정보는 로그 파일에 저장되어 나중에 복구 가능합니다.

### 학생 복구
![복구 화면](./static/images/recover_screen.png)
1. '삭제된 학생 목록' 버튼 클릭
2. 선생님 비밀번호 입력
3. 삭제된 학생 목록 확인 (ID 순 정렬)
4. 복구할 학생 옆의 '복구' 버튼 클릭

![복구 화면](./static/images/recover_check.png)

5. 복구 확인 모달에서 선생님 비밀번호 재입력
6. '복구' 버튼 클릭

> 복구된 학생은 원래 ID를 유지하면서 학생 목록으로 돌아가며, 출석 상태는 초기화됩니다(present = false, code = "", timestamp = null).

### 엑셀 파일 동기화

학생 명단을 엑셀 파일과 동기화하려면:

```bash
python update_students.py
```

이 스크립트는:
- 엑셀 파일에서 최신 학생 명단 가져오기
- 기존 학생의 비밀번호와 출석 상태 유지
- 새로운 학생 추가 및 엑셀에 없는 학생 삭제

다른 엑셀 파일을 사용하려면:
```bash
python update_students.py "다른파일이름.xlsx"
```

## 최신 업데이트

### 2026년 2월 21일 업데이트 - Azure Cosmos DB 통합 ⭐ MAJOR UPDATE

#### 1. 클라우드 데이터 저장소 구현
- **Azure Cosmos DB 통합**: 중요한 데이터가 클라우드에 안전하게 저장됨
  - 학생 정보 (students) - 영구 보관
  - 삭제된 학생 정보 (deleted_students) - 영구 보관
  - 출석 기록 (attendance) - 임시 데이터 (CSV 다운로드로 백업 권장)
- **로컬 폴백**: Cosmos DB 연결 불가 시 JSON 파일 사용 (개발 환경)
- **코호트 격리**: 각 코호트(AI9, AI10, DT3, DT4)의 데이터가 독립적으로 저장됨

#### 2. 보안 강화
- **환경변수 기반 설정**:
  - 교사 비밀번호 (`TEACHER_PASSWORD`)
  - Cosmos DB 연결 정보 (`COSMOS_ENDPOINT`, `COSMOS_KEY`)
  - 코호트 ID (`COHORT_ID`)
- **코드 하드코딩 제거**: 민감한 정보가 더 이상 코드에 없음

#### 3. 확장성 개선
- **코드 재사용성**: 새 코호트 추가 시 환경변수만 변경하면 됨 (코드 복사본 동일)
- **cosmos_service.py**: 모든 데이터 접근을 담당하는 추상화 계층
- **통합 데이터 관리**: 4개 코호트 모두 단일 Cosmos DB에서 관리

#### 4. 데이터 신뢰성
- **Azure App Service idle 문제 해결**: 앱이 멈춰도 Cosmos DB에 데이터 저장
- **삭제된 학생 데이터**: Cosmos DB에 영구 저장되어 복구 가능
- **자동 백업**: Cosmos DB의 자동 백업 기능 활용

#### 5. 마이그레이션 정보
- 기존 JSON 파일은 여전히 폴백용으로 사용 가능
- 기존 프로젝트는 `cosmos_service.py`와 `.env` 파일만 추가하면 마이그레이션 완료
- 환경변수가 없으면 자동으로 JSON 파일 사용

---

### 2025년 10월 1일 업데이트 - 출석부 초기화 버그 수정

#### 1. 출석부 초기화 기능 개선
- **Race Condition 해결**: 출석부 초기화 시 다른 요청이 중간 상태를 읽지 못하도록 `data_lock` 추가
- **캐시 일관성 보장**: 초기화 완료 후 즉시 새 캐시 생성하여 20초 후에도 초기화 상태 유지
- **Atomic 처리**: 학생 데이터 초기화부터 파일 저장, 캐시 재생성까지 한 트랜잭션으로 처리

#### 2. 캐시 무효화 로직 개선
- **`save_attendance()` 함수 개선**: 출석 데이터 저장 시 캐시 무효화 추가
- **파일 수정 시간 추적**: `last_file_modified` 변수를 통한 캐시 유효성 검증 강화

#### 3. 버그 수정
- **출석부 초기화 후 상태 복원 문제 해결**: 초기화 후 약 20초가 지나면 이전 출석 상태로 되돌아가던 버그 수정
- **멀티스레드 환경 안정성 향상**: `data_lock`을 통한 동시성 제어로 스레드 안전성 확보

### 2025년 8월 27일 업데이트 - Azure Web App 최적화

#### 1. 성능 최적화
- **Gunicorn 서버 설정 추가**: Azure Web App free tier에 최적화된 `gunicorn.conf.py` 설정 파일 추가
- **Worker 프로세스 최적화**: Free tier의 메모리 제한을 고려하여 1개 worker로 제한
- **연결 및 요청 수 제한**: worker_connections=500, max_requests=500으로 설정하여 안정성 향상
- **메모리 기반 임시 디렉토리**: `/dev/shm` 사용으로 성능 향상 (가능한 경우)

#### 2. 배포 및 서버 관리 개선
- **Keep Alive 스크립트**: `keep_alive.py` 추가로 Azure Web App의 idle 상태 방지
- **서버 자동 선택**: Waitress 서버 우선 사용, 없으면 Flask 기본 서버로 fallback
- **포트 환경변수 지원**: Azure 환경변수 `PORT`를 자동 인식하여 포트 설정
- **압축 및 캐싱**: Flask-Compress를 통한 gzip 압축 및 정적 파일 캐싱 최적화

#### 3. 안정성 향상
- **동시성 제어**: RLock을 사용한 스레드 안전성 확보
- **파일 캐싱 시스템**: 학생 데이터 파일 변경 감지 및 캐싱으로 성능 개선
- **에러 핸들링**: 예외 상황에 대한 robust한 에러 처리 추가
- **로깅 개선**: 접근 로그 및 에러 로그 포맷 최적화

### 2025년 3월 24일 업데이트

#### 1. 사용자 인터페이스 개선
- **고정 헤더 추가**: 스크롤 시에도 상단 정보(시스템 타이틀, 출석 코드, 출석률, 학생 목록 제목)가 항상 보이도록 고정
- **모달 디자인 개선**: 모달창이 화면 중앙에 표시되도록 개선하고, 모달 열릴 때 헤더가 자동으로 숨겨지도록 개선
- **배경 투명도 개선**: 모달 배경의 투명도를 조정하여 가시성 향상

### 2025년 3월 22일 업데이트

#### 1. 학생 복구 로직 개선
- **출석 상태 초기화 개선**: 삭제된 학생 복구 시 출석 상태가 완전히 초기화(present=false, code="", timestamp=null)
- **유지되는 정보**: 학생 ID, 이름, 비밀번호만 보존되어 기본 정보 유지
- **삭제 마크 제거**: 'deleted_at' 필드가 자동으로 제거되어 삭제 히스토리 정보 제거
- **복구 후 학생 목록 자동 갱신**: ID 순서대로 자동 정렬되어 원래 위치에 학생 표시

#### 2. 사용자 편의 기능 추가
- **일괄 삭제 기능**: 테이블 체크박스를 통해 여러 학생을 선택하여 한번에 삭제 가능
- **빠른 이동 메뉴**: 화면 오른쪽 하단에 상단/학생목록/하단으로 이동할 수 있는 버튼 제공
- **모바일 환경 최적화**: 모든 기능이 모바일에서도 원활하게 작동하도록 개선

### 이전 업데이트 현황

#### 한국 시간대(UTC+9) 적용
- 서버와 클라이언트 시간 불일치 문제 해결
- 모든 시간 관련 기능에 한국 시간 적용

#### 실시간 상태 갱신 개선
- 출석 코드가 유효할 때만 3초마다 학생 목록 자동 새로고침
- 페이지 새로고침 없이 자동 상태 반영

#### 출석 코드 시간 제한 기능
- 5분 유효 시간 제한 적용
- 코드 유효/만료 상태 색상 표시
- 실시간 남은 시간 카운트다운

#### UI/UX 개선
- 모바일 기기 지원 강화 (반응형 테이블, 최적화된 레이아웃)
- 테이블 디자인 개선 (중앙 정렬, 일관된 스타일)
- 직관적인 상태 표시 및 메시지 개선

## 문제 해결

### 출석부 초기화 후 상태 복원 문제 (해결됨)
- **문제**: 출석부 초기화 후 약 20초가 지나면 이전 출석 상태로 되돌아가는 현상
- **원인**: Race condition으로 인해 초기화 중간 상태가 캐시에 저장되어 나중에 복원됨
- **해결**: 2025년 10월 1일 업데이트로 완전히 해결됨
  - `data_lock`을 사용한 atomic 처리
  - 초기화 완료 후 즉시 새 캐시 생성
  - 캐시 무효화 로직 강화

### 학생 복구 기능 오류
- **문제**: 학생 복구 시 "선생님 비밀번호가 올바르지 않습니다" 오류 발생
- **해결 방법**:
  1. 삭제된 학생 목록 모달을 닫고 다시 열어 비밀번호 정확히 입력
  2. 최신 버전의 main.js 파일 확인 (최신 버전에서는 복구 버튼 클릭 시 자동으로 새 비밀번호 입력 모달창 표시)

### 삭제된 학생 정보 오류
- **문제**: 삭제된 학생 목록이 표시되지 않거나 잘못된 정보 표시
- **해결 방법**:
  1. Cosmos DB 연결 확인 (환경변수 `COSMOS_ENDPOINT` 등이 올바르게 설정되었는지 확인)
  2. 로컬 개발 환경: `logs` 폴더 존재 확인 (없으면 생성)
  3. 로컬 개발 환경: `logs/deleted_students.json` 파일 확인 (없으면 비어있는 JSON 배열(`[]`)로 생성)

### Cosmos DB 연결 문제
- **문제**: "Cosmos DB connection failed" 에러 메시지
- **해결 방법**:
  1. 환경변수 확인:
     ```bash
     # .env 파일이 있는지 확인
     ls -la .env

     # 환경변수 값 확인
     echo $COSMOS_ENDPOINT
     echo $COSMOS_KEY
     ```
  2. Azure Cosmos DB 연결 정보 재확인
     - Cosmos DB 계정이 생성되었는지 확인
     - 데이터베이스(`attendance_db`)와 컨테이너(`attendance_data`) 생성 확인
  3. 연결 정보 재입력 및 재시작
  4. 로컬에서는 JSON 파일로 자동 폴백됨

### JavaScript 구문 오류
- **문제**: `Uncaught SyntaxError: Unexpected token '?'` 오류 발생
- **해결 방법**: `static/js/main.js` 파일에서 옵셔널 체이닝 연산자(`?.`)를 논리 연산자로 대체

## 커스터마이징

### 선생님 비밀번호 변경
보안을 위해 `static/js/main.js` 파일과 `app.py` 파일에서 선생님 비밀번호 변경:

1. `static/js/main.js` 파일에서:
```javascript
// 'teacher'를 원하는 비밀번호로 변경
if (teacherPassword !== '새로운비밀번호') {
```

2. `app.py` 파일에서도 변경:
```python
# 관련 코드 모두 업데이트
if teacher_password != '새로운비밀번호':
```

### Favicon 변경
웹 브라우저 탭 아이콘 변경:

1. 원하는 이미지 파일을 `static` 폴더에 저장
2. `templates/index.html` 파일의 `<head>` 섹션에서 참조 경로 수정

### 수동 학생 명단 입력
기본 엑셀 파일 처리가 요구사항에 맞지 않는 경우:

```python
# 예시: 수동으로 학생 목록 입력
student_names = [
    "김민준", "이서연", "이수민", "박지호", "정우진"
]
manual_students = create_students_manually(student_names)
save_students_to_json(manual_students)
```

## 새로운 코호트 추가 방법

이제 새로운 교육과정이 시작될 때 매우 간단하게 추가할 수 있습니다!

### 방법 1: 코드 복사 후 환경변수 변경 (권장)

```bash
# 기존 프로젝트 복사
cp -r msai10-attend msai11-attend

# 새 프로젝트 폴더로 이동
cd msai11-attend

# .env 파일 생성 (또는 .env.example 복사)
cp .env.example .env

# .env 파일에서 COHORT_ID 변경
# COHORT_ID=AI10 → COHORT_ID=AI11 (또는 DT5, 등)
```

### Azure App Service에서 배포

1. 새 App Service 생성 (또는 기존 복사)
2. Configuration → Application settings에서 `COHORT_ID` 변경
   - 예: `AI10` → `AI11`
3. 다른 설정은 모두 동일하게 유지:
   - `COSMOS_ENDPOINT`
   - `COSMOS_KEY`
   - `COSMOS_DB`
   - `COSMOS_CONTAINER`
   - `TEACHER_PASSWORD`

> ⚠️ **중요**: 각 App Service는 **다른 COHORT_ID**를 가져야 합니다!

### 결과

- 모든 코호트 데이터는 **하나의 Cosmos DB**에 저장됨
- 코호트별 데이터는 `/cohort_id` partition key로 자동 격리됨
- 통합 대시보드 또는 보고서 작성 시 모든 코호트 데이터 접근 가능

---

이 출석 관리 시스템은 교육 환경에서 출석 관리를 간소화하고 효율화하기 위한 웹 애플리케이션입니다. Azure Cosmos DB를 통해 안전한 클라우드 저장소를 제공하고, 학생별 비밀번호 인증을 통해 출석 체크의 정확성을 높이며, 출석 데이터를 자동으로 저장하고 내보낼 수 있어 관리가 용이합니다. 학생 삭제/복구 기능과 엑셀 동기화 도구를 통해 학생 명단 변경도 효율적으로 관리할 수 있으며, 환경변수 기반 설정으로 보안을 강화했습니다.
