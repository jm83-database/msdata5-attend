from flask import Flask, render_template, jsonify, request, Response
from flask_compress import Compress
import os
import json
import datetime
import csv
from io import StringIO
from threading import RLock
import time
from cosmos_service import CosmosService

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # 1시간 캐시
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']

# Flask-Compress 초기화 (gzip 압축 활성화)
Compress(app)

# 응답 압축을 위한 미들웨어
@app.after_request
def after_request(response):
    # gzip 압축 활성화 (Azure에서 자동 처리되므로 헤더만 설정)
    if response.content_type.startswith('text/') or 'application/json' in response.content_type:
        response.headers['Vary'] = 'Accept-Encoding'

    # 캐시 헤더 설정
    if request.endpoint == 'static':
        response.cache_control.max_age = 86400  # 24시간 캐시
        response.cache_control.public = True
    elif request.endpoint in ['get_students', 'get_code']:
        response.cache_control.no_cache = True
        response.cache_control.must_revalidate = True

    return response

# Azure Cosmos DB 서비스 초기화 (cohort_id는 환경변수에서 자동 로드)
db_service = CosmosService()

# 출석 데이터를 저장할 변수
students = []
current_code = ""
code_generation_time = None

# 캐싱 및 동시성 제어
data_lock = RLock()
students_cache = None
last_cache_time = None
cache_timeout = 30  # 30초 캐시

# 교사 비밀번호 (환경변수 TEACHER_PASSWORD에서 로드, 기본값: 'teacher')
TEACHER_PASSWORD = os.environ.get('TEACHER_PASSWORD', 'teacher')

def get_cached_students():
    """캐시된 학생 목록을 반환하거나 새로 로드합니다."""
    global students, students_cache, last_cache_time

    with data_lock:
        current_time = time.time()

        # 캐시가 유효한지 확인 (30초 이내)
        if (students_cache is not None and
            last_cache_time is not None and
            current_time - last_cache_time < cache_timeout):
            students = students_cache
            return students

        # 캐시 무효화 또는 처음 로드
        students = db_service.load_students()

        # 캐시 업데이트
        students_cache = students.copy() if students else []
        last_cache_time = current_time

        return students

def load_students():
    """호환성을 위한 래퍼 함수"""
    return get_cached_students()

def save_students_to_db():
    """학생 데이터를 데이터베이스에 저장합니다."""
    global students_cache, last_cache_time
    try:
        with data_lock:
            db_service.save_students(students)
            # 캐시 무효화
            students_cache = None
            last_cache_time = None
    except Exception as e:
        print(f"학생 데이터 저장 중 오류 발생: {e}")

def save_students():
    """호환성을 위한 래퍼 함수"""
    return save_students_to_db()

def save_attendance():
    """출석 상태를 데이터베이스에 저장합니다."""
    global students_cache, last_cache_time
    try:
        # UTC+9(한국 시간) 적용
        current_time = datetime.datetime.now() + datetime.timedelta(hours=9)
        attendance_data = {
            "date": current_time.strftime("%Y-%m-%d"),
            "time": current_time.strftime("%H:%M:%S"),
            "students": students
        }

        # 기존 출석 기록 로드
        all_attendance = db_service.load_attendance()

        # 오늘 날짜의 기록이 있는지 확인
        today = attendance_data["date"]
        updated = False
        for i, record in enumerate(all_attendance):
            if record.get("date") == today:
                all_attendance[i] = attendance_data
                updated = True
                break

        # 오늘 기록이 없으면 추가
        if not updated:
            all_attendance.append(attendance_data)

        # 저장
        db_service.save_attendance(all_attendance)

        # 캐시 무효화
        students_cache = None
        last_cache_time = None
    except Exception as e:
        print(f"출석 데이터 저장 중 오류 발생: {e}")

# 애플리케이션 시작 시 학생 목록 로드
get_cached_students()

# 메인 페이지
@app.route('/')
def index():
    response = render_template('index.html')
    return response

# API 엔드포인트: 학생 목록 가져오기 (비밀번호 제외)
@app.route('/api/students', methods=['GET'])
def get_students():
    # 캐시된 학생 목록 사용
    current_students = get_cached_students()

    # 비밀번호를 제외한 학생 정보만 반환 (list comprehension으로 최적화)
    students_without_password = [
        {k: v for k, v in student.items() if k != 'password'}
        for student in current_students
    ]
    return jsonify(students_without_password)

# API 엔드포인트: 학생 이름 목록 가져오기
@app.route('/api/student-names', methods=['GET'])
def get_student_names():
    current_students = get_cached_students()
    names = [{"id": student["id"], "name": student["name"]} for student in current_students]
    return jsonify(names)

# API 엔드포인트: 출석 코드 가져오기
@app.route('/api/code', methods=['GET'])
def get_code():
    generation_time = ""
    is_valid = False
    is_expired = False
    time_remaining = 0

    if code_generation_time and current_code:
        generation_time = code_generation_time.strftime("%Y-%m-%d %H:%M:%S")
        # 코드 생성 후 경과 시간 계산 (초 단위)
        import datetime
        # UTC+9(한국 시간) 적용
        current_time = datetime.datetime.now() + datetime.timedelta(hours=9)
        elapsed_seconds = (current_time - code_generation_time).total_seconds()

        # 5분(300초) 유효 시간 설정
        validity_period = 300

        # 유효 시간 이내인지 확인
        is_valid = elapsed_seconds < validity_period
        is_expired = not is_valid and current_code != ""

        # 남은 시간 계산 (초 단위)
        time_remaining = max(0, validity_period - elapsed_seconds) if is_valid else 0

    return jsonify({
        "code": current_code,
        "generationTime": generation_time,
        "isValid": is_valid,
        "isExpired": is_expired,
        "timeRemaining": int(time_remaining)
    })

# API 엔드포인트: 새 출석 코드 생성 (수동으로만 생성)
@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    import random
    import string
    import datetime
    global current_code, code_generation_time

    # 교사 비밀번호 확인 (환경변수 사용)
    data = request.json
    teacher_password = data.get('teacher_password')

    if teacher_password != TEACHER_PASSWORD:
        return jsonify({"success": False, "message": "선생님 비밀번호가 올바르지 않습니다."}), 401

    # 새 코드 생성
    current_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code_generation_time = datetime.datetime.now() + datetime.timedelta(hours=9)  # UTC+9(한국 시간) 적용

    # 코드 생성 로그 기록
    print(f"새 출석 코드 생성: {current_code} (생성 시간: {code_generation_time})")

    return jsonify({
        "success": True,
        "code": current_code,
        "generationTime": code_generation_time.strftime("%Y-%m-%d %H:%M:%S")
    })

# API 엔드포인트: 출석 확인하기 (비밀번호 확인 추가)
@app.route('/api/attendance', methods=['POST'])
def check_attendance():
    global students
    data = request.json
    student_name = data.get('name')
    student_code = data.get('code')
    student_password = data.get('password')  # 비밀번호 추가

    if not student_name or not student_code or not student_password:
        return jsonify({"success": False, "message": "이름, 코드, 비밀번호를 모두 입력해야 합니다."}), 400

    # 코드가 일치하는지 확인
    if student_code != current_code:
        return jsonify({"success": False, "message": "출석 코드가 일치하지 않습니다."}), 400

    # 코드가 유효한지 확인 (5분 이내)
    if code_generation_time:
        import datetime
        # UTC+9(한국 시간) 적용
        current_time = datetime.datetime.now() + datetime.timedelta(hours=9)
        elapsed_seconds = (current_time - code_generation_time).total_seconds()
        if elapsed_seconds > 300:  # 5분(300초) 초과
            return jsonify({"success": False, "message": "출석 코드가 만료되었습니다. 새로운 코드를 요청하세요."}), 400

    for i, student in enumerate(students):
        if student['name'].lower() == student_name.lower():
            # 비밀번호 확인 추가
            if student['password'] != student_password:
                return jsonify({"success": False, "message": "비밀번호가 일치하지 않습니다."}), 400

            import datetime
            # UTC+9(한국 시간) 적용
            current_time = datetime.datetime.now() + datetime.timedelta(hours=9)
            students[i]['present'] = True
            students[i]['code'] = student_code
            students[i]['timestamp'] = current_time.strftime("%H:%M:%S")

            # 출석 정보 저장
            save_students_to_db()
            save_attendance()

            return jsonify({"success": True, "message": "출석이 확인되었습니다!"})

    return jsonify({"success": False, "message": "명단에 없는 학생입니다."}), 404

# API 엔드포인트: 출석부 초기화
@app.route('/api/attendance/reset', methods=['POST'])
def reset_attendance():
    global students, students_cache, last_cache_time

    try:
        # Race condition 방지: 전체 초기화 과정을 atomic하게 처리
        with data_lock:
            # 1단계: students 변수 초기화
            for i in range(len(students)):
                students[i]['present'] = False
                students[i]['code'] = ""
                students[i]['timestamp'] = None

            # 2단계: 캐시 무효화 (즉시 반영)
            students_cache = None
            last_cache_time = None

            # 3단계: 학생 데이터 저장
            db_service.save_students(students)

            # 4단계: 출석 기록 초기화
            db_service.save_attendance([])

            # 5단계: 현재 상태(초기화된 상태)를 attendance에 저장
            current_time = datetime.datetime.now() + datetime.timedelta(hours=9)
            attendance_data = {
                "date": current_time.strftime("%Y-%m-%d"),
                "time": current_time.strftime("%H:%M:%S"),
                "students": students
            }
            db_service.save_attendance([attendance_data])

            # 6단계: 초기화된 상태로 캐시 재생성 (중요!)
            students_cache = students.copy() if students else []
            last_cache_time = time.time()

        print(f"출석부 초기화 완료: {len(students)}명의 학생 출석 상태 초기화")

        return jsonify({"success": True, "message": "모든 출석 기록이 초기화되었습니다."})
    except Exception as e:
        print(f"출석부 초기화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

# CSV 다운로드 API 엔드포인트 (삭제된 학생 제외)
@app.route('/api/attendance/download', methods=['GET'])
def download_attendance_csv():
    try:
        # 출석 기록 로드
        attendance_records = db_service.load_attendance()

        # 현재 학생 ID 목록 (현재 활성화된 학생들만)
        active_student_ids = [student['id'] for student in students]

        # CSV 데이터 생성을 위한 메모리 버퍼
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        # CSV 헤더 작성
        csv_writer.writerow(['날짜', '학생ID', '이름', '출석여부', '출석코드', '출석시간'])

        # 모든 출석 기록을 CSV 형식으로 변환 (삭제된 학생 제외)
        for record in attendance_records:
            date = record.get('date', '')
            for student in record.get('students', []):
                # 현재 활성화된 학생 ID 목록에 있는 학생만 포함
                if student.get('id') in active_student_ids:
                    csv_writer.writerow([
                        date,
                        student.get('id', ''),
                        student.get('name', ''),
                        '출석' if student.get('present', False) else '미출석',
                        student.get('code', ''),
                        student.get('timestamp', '')
                    ])

        # 메모리 버퍼의 내용을 파일로 다운로드
        csv_buffer.seek(0)

        # 현재 날짜와 시간으로 파일명 생성 (년월일_시분)
        # UTC+9(한국 시간) 적용
        now = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y%m%d_%H%M")
        filename = f"attendance_{now}.csv"

        return Response(
            csv_buffer.getvalue().encode('utf-8-sig'),  # UTF-8 with BOM for Excel compatibility
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )

    except Exception as e:
        print(f"CSV 다운로드 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

# 학생 삭제 API 추가
@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    global students

    # 선생님 비밀번호 확인
    data = request.json
    teacher_password = data.get('teacher_password')

    if teacher_password != TEACHER_PASSWORD:
        return jsonify({"success": False, "message": "선생님 비밀번호가 올바르지 않습니다."}), 401

    # 학생 ID로 학생 찾기
    student_to_delete = None
    for i, student in enumerate(students):
        if student['id'] == student_id:
            student_to_delete = students.pop(i)
            break

    if student_to_delete:
        # 삭제 로그 저장 (복구 가능하도록)
        db_service.add_deleted_student(student_to_delete)

        # 변경된 학생 목록 저장
        save_students_to_db()

        return jsonify({
            "success": True,
            "message": f"{student_to_delete['name']} 학생이 삭제되었습니다.",
            "deleted_student": student_to_delete
        })
    else:
        return jsonify({"success": False, "message": "해당 ID의 학생을 찾을 수 없습니다."}), 404

# 삭제된 학생 목록 조회 API
@app.route('/api/students/deleted', methods=['GET'])
def get_deleted_students():
    try:
        # 선생님 비밀번호 확인
        teacher_password = request.args.get('teacher_password')

        if teacher_password != TEACHER_PASSWORD:
            return jsonify({"success": False, "message": "선생님 비밀번호가 올바르지 않습니다."}), 401

        # 삭제된 학생 목록 로드
        deleted_students = db_service.load_deleted_students()
        return jsonify(deleted_students)

    except Exception as e:
        print(f"삭제된 학생 목록 조회 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

# 삭제된 학생 복구 API
@app.route('/api/students/restore', methods=['POST'])
def restore_student():
    global students

    try:
        data = request.json
        try:
            student_id = int(data.get('student_id'))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "학생 ID가 유효하지 않습니다."}), 400
        teacher_password = data.get('teacher_password')

        if teacher_password != TEACHER_PASSWORD:
            return jsonify({"success": False, "message": "선생님 비밀번호가 올바르지 않습니다."}), 401

        # 삭제된 학생 목록 로드
        deleted_students = db_service.load_deleted_students()

        # ID로 학생 찾기
        student_to_restore = None
        for i, student in enumerate(deleted_students):
            if student['id'] == student_id:
                student_to_restore = deleted_students.pop(i)
                break

        if not student_to_restore:
            return jsonify({"success": False, "message": "해당 ID의 삭제된 학생을 찾을 수 없습니다."}), 404

        # 삭제 시간 정보 제거
        if 'deleted_at' in student_to_restore:
            del student_to_restore['deleted_at']

        # 출석 상태 초기화
        student_to_restore['present'] = False
        student_to_restore['code'] = ""
        student_to_restore['timestamp'] = None

        # 학생 목록에 복구
        students.append(student_to_restore)

        # 업데이트된 목록 저장
        save_students_to_db()

        # 업데이트된 삭제 로그 저장
        db_service.save_deleted_students(deleted_students)

        return jsonify({
            "success": True,
            "message": f"{student_to_restore['name']} 학생이 복구되었습니다.",
            "restored_student": student_to_restore
        })

    except Exception as e:
        print(f"학생 복구 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

# 일괄 삭제 API
@app.route('/api/students/bulk-delete', methods=['POST'])
def bulk_delete_students():
    global students

    try:
        data = request.json
        student_ids = data.get('student_ids', [])
        teacher_password = data.get('teacher_password')

        # 선생님 비밀번호 확인
        if teacher_password != TEACHER_PASSWORD:
            return jsonify({"success": False, "message": "선생님 비밀번호가 올바르지 않습니다."}), 401

        if not student_ids or not isinstance(student_ids, list):
            return jsonify({"success": False, "message": "삭제할 학생 ID가 지정되지 않았습니다."}), 400

        deleted_count = 0
        deleted_students_info = []

        # 삭제할 학생 찾기 (정수 ID로 변환 후 비교)
        student_ids = [int(id) for id in student_ids if str(id).isdigit()]

        for student_id in student_ids:
            # 학생 ID로 학생 찾기
            for i, student in enumerate(students):
                if student['id'] == student_id:
                    student_to_delete = students.pop(i)
                    # 삭제 로그 저장 (복구 가능하도록)
                    db_service.add_deleted_student(student_to_delete)
                    deleted_students_info.append({
                        'id': student_to_delete['id'],
                        'name': student_to_delete['name']
                    })
                    deleted_count += 1
                    break

        # 변경된 학생 목록 저장
        save_students_to_db()

        return jsonify({
            "success": True,
            "message": f"{deleted_count}명의 학생이 삭제되었습니다.",
            "deleted_count": deleted_count,
            "deleted_students": deleted_students_info
        })

    except Exception as e:
        print(f"학생 일괄 삭제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

# 학생 비밀번호 다운로드 엔드포인트 (교사용)
@app.route('/api/students/passwords', methods=['GET'])
def download_student_passwords():
    try:
        # CSV 데이터 생성을 위한 메모리 버퍼
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        # CSV 헤더 작성
        csv_writer.writerow(['학생ID', '이름', '비밀번호'])

        # 학생 비밀번호 정보를 CSV 형식으로 변환
        for student in students:
            csv_writer.writerow([
                student.get('id', ''),
                student.get('name', ''),
                student.get('password', '')
            ])

        # 메모리 버퍼의 내용을 파일로 다운로드
        csv_buffer.seek(0)

        # 현재 날짜로 파일명 생성
        # UTC+9(한국 시간) 적용
        now = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y%m%d_%H%M")
        filename = f"student_passwords_{now}.csv"

        return Response(
            csv_buffer.getvalue().encode('utf-8-sig'),  # UTF-8 with BOM for Excel compatibility
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )

    except Exception as e:
        print(f"비밀번호 다운로드 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"오류 발생: {e}"}), 500

if __name__ == '__main__':
    # 개발 환경에서만 Flask 내장 서버 사용
    if os.environ.get('FLASK_ENV') == 'development':
        print("Flask 개발 서버를 사용합니다.")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # 프로덕션 환경에서는 Gunicorn 또는 Waitress 사용
        try:
            from waitress import serve
            port = int(os.environ.get('PORT', 8000))
            print(f"Waitress 서버 시작: 포트 {port}")
            serve(app, host='0.0.0.0', port=port, threads=4, cleanup_interval=30)
        except ImportError:
            print("기본 Flask 서버를 사용합니다.")
            port = int(os.environ.get('PORT', 8000))
            app.run(host='0.0.0.0', port=port, threaded=True)
        except Exception as e:
            print(f"서버 시작 중 오류 발생: {e}")
