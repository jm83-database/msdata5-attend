import pandas as pd
import json
import os
import datetime
import random
import string

def update_students_from_excel(excel_file, json_file='students.json'):
    """
    Excel 파일에서 최신 학생 목록을 읽어와 JSON 파일을 업데이트합니다.
    기존 학생 정보(비밀번호, 출석 상태 등)는 유지하면서 새 학생을 추가하고
    Excel에 없는 학생은 삭제합니다.
    """
    try:
        # 1. 기존 students.json 불러오기
        current_students = []
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                current_students = json.load(f)
            print(f"기존 학생 {len(current_students)}명의 정보를 로드했습니다.")
        
        # 2. Excel에서 새 학생 목록 추출
        new_students_raw = extract_students_with_duplicates(excel_file)
        
        # 3. 새 학생 목록에 고유 ID 할당 및 이름 중복 처리
        new_students = process_duplicates(new_students_raw)
        print(f"Excel에서 {len(new_students)}명의 학생 정보를 추출했습니다.")
        
        # 4. 학생 목록 비교 및 업데이트
        updated_students, added, removed, preserved = merge_student_lists(current_students, new_students)
        
        # 5. 변경 사항 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(updated_students, f, ensure_ascii=False, indent=4)
        
        # 6. 로그 저장 (삭제된 학생 기록)
        log_removed_students(removed)
        
        # 7. 결과 요약 출력
        print("\n===== 학생 명단 업데이트 결과 =====")
        print(f"유지된 학생: {len(preserved)}명")
        print(f"추가된 학생: {len(added)}명")
        print(f"삭제된 학생: {len(removed)}명")
        print(f"최종 학생 수: {len(updated_students)}명")
        print("==================================\n")
        
        # 8. 변경된 학생 목록 출력
        if added:
            print("추가된 학생:")
            for student in added:
                print(f"  - {student['name']} (ID: {student['id']})")
        
        if removed:
            print("\n삭제된 학생:")
            for student in removed:
                print(f"  - {student['name']} (ID: {student['id']})")
        
        return updated_students
    
    except Exception as e:
        print(f"학생 명단 업데이트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_students_with_duplicates(excel_file):
    """Excel 파일에서 학생 이름을 추출합니다."""
    try:
        # Excel 파일의 모든 시트 이름 가져오기
        xl = pd.ExcelFile(excel_file)
        sheet_names = xl.sheet_names
        print(f"엑셀 파일에서 발견된 시트: {sheet_names}")
        
        raw_students = []
        
        # 각 시트별로 처리
        for sheet_name in sheet_names:
            # 여러 가능한 헤더 위치 시도
            for header_row in [None, 0, 1]:
                try:
                    if header_row is None:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    else:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                    
                    # 이름 열 찾기
                    name_column = None
                    
                    # 헤더가 있는 경우 열 이름으로 찾기
                    if header_row is not None:
                        name_columns = ['이름', 'Name', '성명', '학생명', '이름(Full Name)', 'Full Name', '성함']
                        for col in name_columns:
                            if col in df.columns:
                                name_column = col
                                print(f"'{sheet_name}' 시트에서 이름 열을 찾았습니다: '{col}'")
                                break
                    
                    # 이름 열을 찾지 못했거나 헤더가 없는 경우
                    if name_column is None:
                        # 첫 번째 열 사용
                        name_column = 0
                        print(f"'{sheet_name}' 시트에서 이름 열을 찾지 못해 첫 번째 열을 사용합니다.")
                    
                    # 데이터 시작 행 결정
                    start_row = 0 if header_row is not None else 1
                    
                    # 학생 데이터 추출
                    students_in_sheet = []
                    for _, row in df.iloc[start_row:].iterrows():
                        # 이름 값 가져오기
                        if isinstance(name_column, (int, float)):
                            name_value = str(row.iloc[name_column]).strip()
                        else:
                            name_value = str(row[name_column]).strip()
                        
                        # 빈 값이나 NaN이 아닌 경우만 처리
                        if name_value and name_value.lower() != 'nan' and len(name_value) > 0:
                            students_in_sheet.append({"name": name_value, "original_name": name_value})
                    
                    if students_in_sheet:
                        print(f"{len(students_in_sheet)}명의 학생을 '{sheet_name}' 시트에서 추출했습니다.")
                        raw_students.extend(students_in_sheet)
                        break  # 성공하면 다음 시트로
                    
                except Exception as e:
                    print(f"'{sheet_name}' 시트 처리 중 오류 발생: {e}")
                    continue
        
        return raw_students
    
    except Exception as e:
        print(f"Excel 파일 처리 중 오류 발생: {e}")
        return []

def process_duplicates(raw_students):
    """
    학생 목록에서 동명이인을 처리하고 고유 ID를 할당합니다.
    """
    # 이름 중복 확인
    name_counter = {}
    for student in raw_students:
        name = student["original_name"]
        if name in name_counter:
            name_counter[name] += 1
        else:
            name_counter[name] = 1
    
    # 중복 이름에 대한 인덱스 추적
    name_indices = {name: [] for name in name_counter if name_counter[name] > 1}
    
    # 최종 학생 목록
    processed_students = []
    
    # 학생 ID 부여 (1부터 시작)
    student_id = 1
    
    for student in raw_students:
        name = student["original_name"]
        final_name = name
        
        # 동명이인 처리
        if name_counter[name] > 1:
            current_index = len(name_indices[name])
            suffix = chr(65 + current_index)  # A=65, B=66, ...
            final_name = f"{name}{suffix}"
            name_indices[name].append(final_name)
        
        # 최종 학생 객체 생성
        student_obj = {
            "id": student_id,
            "name": final_name,
            "present": False,
            "code": "",
            "timestamp": None,
            "password": generate_password()
        }
        
        processed_students.append(student_obj)
        student_id += 1
    
    return processed_students

def merge_student_lists(current_students, new_students):
    """
    기존 학생 목록과 새로운 학생 목록을 병합합니다.
    기존 학생의 정보(비밀번호, 출석 상태 등)는 유지됩니다.
    """
    # 현재 학생 이름 -> 학생 객체 매핑
    current_by_name = {s["name"]: s for s in current_students}
    
    # 업데이트된 학생 목록, 추가/삭제 학생 추적
    updated_students = []
    added_students = []
    preserved_students = []
    
    # 새 학생 목록을 기준으로 업데이트
    for new_student in new_students:
        if new_student["name"] in current_by_name:
            # 기존 학생 정보 유지
            existing = current_by_name[new_student["name"]]
            
            # ID는 새 목록의 ID로 업데이트
            existing["id"] = new_student["id"]
            
            updated_students.append(existing)
            preserved_students.append(existing)
        else:
            # 새 학생 추가
            updated_students.append(new_student)
            added_students.append(new_student)
    
    # 삭제된 학생 찾기
    new_by_name = {s["name"]: s for s in new_students}
    removed_students = [s for s in current_students if s["name"] not in new_by_name]
    
    return updated_students, added_students, removed_students, preserved_students

def generate_password(length=4):
    """임의의 숫자 비밀번호를 생성합니다."""
    return ''.join(random.choices(string.digits, k=length))

def log_removed_students(removed_students):
    """삭제된 학생 정보를 로그 파일에 저장합니다."""
    if not removed_students:
        return
    
    try:
        # 로그 디렉토리 확인 및 생성
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 로그 파일 경로
        log_file = os.path.join(log_dir, 'deleted_students.json')
        
        # 기존 로그 불러오기
        deleted_students = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                deleted_students = json.load(f)
        
        # 현재 시간 추가
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 삭제된 학생 정보 추가
        for student in removed_students:
            student['deleted_at'] = current_time
            deleted_students.append(student)
        
        # 로그 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(deleted_students, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"삭제 로그 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    # 기본 엑셀 파일 경로
    excel_file = "MS AI School 9기 Teams 계정.xlsx"
    
    # 명령줄 인자로 다른 파일을 지정할 수 있음
    import sys
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    
    print(f"Excel 파일 '{excel_file}'에서 학생 정보를 읽어 업데이트합니다...")
    
    # 학생 정보 업데이트
    updated_students = update_students_from_excel(excel_file)
    
    if updated_students:
        print("학생 명단 업데이트가 완료되었습니다.")
    else:
        print("학생 명단 업데이트에 실패했습니다.")
