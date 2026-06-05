import json
import os
import random
import string

def generate_password(length=4):
    """간단한 숫자 비밀번호 생성"""
    return ''.join(random.choices(string.digits, k=length))

def add_passwords_to_students(json_file='students.json'):
    """기존 students.json 파일에 각 학생에게 비밀번호 추가"""
    if not os.path.exists(json_file):
        print(f"파일을 찾을 수 없습니다: {json_file}")
        return False
    
    try:
        # 기존 학생 데이터 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            students = json.load(f)
        
        # 각 학생에게 비밀번호 추가
        for student in students:
            # 이미 비밀번호가 있는지 확인
            if 'password' not in student:
                # 4자리 숫자 비밀번호 생성
                student['password'] = generate_password()
        
        # 업데이트된 데이터 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(students, f, ensure_ascii=False, indent=4)
        
        print(f"{len(students)}명의 학생에게 비밀번호를 추가했습니다.")
        print("학생 비밀번호 정보:")
        for student in students:
            print(f"ID: {student['id']}, 이름: {student['name']}, 비밀번호: {student['password']}")
        
        return True
    
    except Exception as e:
        print(f"학생 비밀번호 추가 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    add_passwords_to_students()