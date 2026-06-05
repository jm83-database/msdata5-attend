import pandas as pd
import json
import os

def extract_students_with_duplicates(excel_file):
    """
    Excel 파일에서 학생 정보를 읽어 students 리스트로 변환합니다.
    동명이인은 이름 뒤에 A, B, C 등을 붙여 구분합니다.
    """
    try:
        # Excel 파일의 모든 시트 이름 가져오기
        xl = pd.ExcelFile(excel_file)
        sheet_names = xl.sheet_names
        print(f"엑셀 파일에서 발견된 시트: {sheet_names}")
        
        raw_students = []  # 원래 이름으로 먼저 모든 학생 정보를 저장
        student_id = 1  # 전체 학생에 대한 ID
        
        # 각 시트별로 처리하여 raw_students에 먼저 모든 학생 정보 수집
        for sheet_name in sheet_names:
            print(f"\n--- '{sheet_name}' 시트 처리 중 ---")
            
            # 여러 가능한 헤더 위치 시도
            for header_row in [None, 0, 1]:
                try:
                    if header_row is None:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    else:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                    
                    # 데이터 미리보기
                    print("데이터 미리보기:")
                    print(df.head(3))
                    
                    # 이름 열 찾기
                    name_column = None
                    
                    # 헤더가 있는 경우 열 이름으로 찾기
                    if header_row is not None:
                        name_columns = ['이름', 'Name', '성명', '학생명', '이름(Full Name)', 'Full Name', '성함']
                        for col in name_columns:
                            if col in df.columns:
                                name_column = col
                                print(f"이름 열을 찾았습니다: '{col}'")
                                break
                    
                    # 이름 열을 찾지 못했거나 헤더가 없는 경우
                    if name_column is None:
                        # 첫 번째 또는 두 번째 열 사용
                        name_column = 0  # 첫 번째 열
                        print(f"이름 열을 찾지 못해 첫 번째 열을 사용합니다.")
                    
                    # 데이터 시작 행 결정
                    start_row = 0
                    if header_row is not None:
                        start_row = 0  # pandas가 이미 헤더를 제외함
                    else:
                        start_row = 1
                    
                    students_in_sheet = []
                    
                    # 학생 데이터 추출 - 일단 원래 이름 그대로 저장
                    for idx, (_, row) in enumerate(df.iloc[start_row:].iterrows()):
                        # 이름 값 가져오기
                        if isinstance(name_column, (int, float)):
                            name_value = str(row.iloc[name_column]).strip()
                        else:
                            name_value = str(row[name_column]).strip()
                        
                        # 빈 값이나 NaN이 아닌 경우만 처리
                        if name_value and name_value.lower() != 'nan' and len(name_value) > 0:
                            student = {
                                "id": student_id,
                                "name": name_value,  # 원래 이름 그대로 저장
                                "present": False,
                                "code": "",
                                "timestamp": None,
                                "original_name": name_value  # 원래 이름도 저장해 둠
                            }
                            students_in_sheet.append(student)
                            student_id += 1  # 다음 학생 ID
                    
                    if students_in_sheet:
                        print(f"{len(students_in_sheet)}명의 학생을 '{sheet_name}' 시트에서 추출했습니다.")
                        raw_students.extend(students_in_sheet)
                        break  # 성공적으로 데이터를 추출했으면 다음 헤더 위치 시도 중단
                    else:
                        print(f"'{sheet_name}' 시트에서 학생 데이터를 찾지 못했습니다. 다른 헤더 위치 시도.")
                
                except Exception as e:
                    print(f"헤더 행 {header_row}로 시도 중 오류 발생: {e}")
                    continue
        
        # 이름 중복 확인 및 처리
        name_counter = {}
        # 이름별 등장 인덱스 기록
        name_indices = {}
        final_students = []
        
        # 먼저 모든 이름의 등장 횟수를 카운트
        for student in raw_students:
            name = student["original_name"]
            if name in name_counter:
                name_counter[name] += 1
            else:
                name_counter[name] = 1
                
        # 중복 있는 이름에 대해 인덱스 배열 초기화
        for name, count in name_counter.items():
            if count > 1:
                name_indices[name] = []
        
        # 이름 중복에 따라 최종 이름 결정
        for student in raw_students:
            name = student["original_name"]
            
            if name_counter[name] > 1:
                # 이 이름에 대한 전체 인덱스 개수 확인
                current_index = len(name_indices[name])
                
                # 새 이름 부여 (첫 번째는 A, 두 번째는 B, ...)
                new_name = f"{name}{chr(65 + current_index)}"  # A=65, B=66, ...
                student["name"] = new_name
                
                # 이 이름이 처리되었음을 기록
                name_indices[name].append(new_name)
            
            # 더 이상 필요 없는 original_name 필드 제거
            if "original_name" in student:
                del student["original_name"]
            
            final_students.append(student)
        
        # 디버깅을 위한 동명이인 처리 결과 출력
        print("\n동명이인 처리 결과:")
        for name, variants in name_indices.items():
            print(f"{name}: {', '.join(variants)}")
        
        print(f"\n총 {len(final_students)}명의 학생 데이터를 추출했습니다.")
        return final_students
    
    except Exception as e:
        print(f"Excel 파일 처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

def create_students_manually(names):
    """
    학생 이름 목록으로부터 students.json 파일을 생성합니다.
    동명이인은 자동으로 처리합니다.
    
    예시:
    names = ["김민준", "이서연", "이수민", "이수민", "박지호"]
    결과: 이수민A, 이수민B로 저장됩니다.
    """
    # 일단 중복 체크할 이름을 정리
    processed_names = [name.strip() for name in names if name.strip()]
    
    # 이름별 등장 횟수 계산
    name_count = {}
    for name in processed_names:
        if name in name_count:
            name_count[name] += 1
        else:
            name_count[name] = 1
    
    # 결과 딕셔너리 준비 (각 고유 이름에 인덱스 할당)
    name_indices = {name: [] for name in name_count if name_count[name] > 1}
    
    # 최종 결과물
    students = []
    
    # 모든 이름에 대해 처리
    for idx, name in enumerate(processed_names):
        final_name = name
        
        # 이 이름이 중복되는 이름인 경우
        if name_count[name] > 1:
            # 이미 처리된 같은 이름의 수를 확인
            same_name_count = len(name_indices[name])
            
            # 접미사 추가 (A, B, C, ...)
            suffix = chr(65 + same_name_count)  # A=65, B=66, ...
            final_name = f"{name}{suffix}"
            
            # 이 이름이 처리되었음을 기록
            name_indices[name].append(final_name)
        
        # 학생 객체 생성
        student = {
            "id": idx + 1,
            "name": final_name,
            "present": False,
            "code": "",
            "timestamp": None
        }
        students.append(student)
    
    # 디버깅 출력
    print("\n동명이인 처리 결과:")
    for name, variants in name_indices.items():
        print(f"{name}: {', '.join(variants)}")
    
    return students

def save_students_to_json(students, json_file='students.json'):
    """학생 데이터를 JSON 파일로 저장합니다."""
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(students, f, ensure_ascii=False, indent=4)
        print(f"{len(students)}명의 학생 정보가 {json_file}에 저장되었습니다.")
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생: {e}")

# 사용 예시
if __name__ == "__main__":
    try:
        # Excel 파일에서 학생 데이터 추출
        excel_file = "MS Data School 5기 Teams 계정.xlsx"
        students = extract_students_with_duplicates(excel_file)
        
        if students:
            # JSON 파일로 저장
            save_students_to_json(students)
            
            # 출력하여 확인
            print("\n변환된 학생 목록 (처음 10명):")
            for student in students[:10]:  # 처음 10명만 출력
                print(f"ID: {student['id']}, 이름: {student['name']}")
            
            if len(students) > 10:
                print(f"... 외 {len(students) - 10}명")
        else:
            print("Excel 파일에서 학생 데이터를 추출할 수 없습니다.")
            
            # 수동으로 학생 목록 입력 (테스트)
            print("\nExcel 처리에 실패했습니다. 수동으로 학생 목록을 입력하세요.")
            student_names = [
                "김민준", "이서연", "이수민", "이수민", "박지호", "정우진", "최수아", "이수민"
            ]
            manual_students = create_students_manually(student_names)
            save_students_to_json(manual_students)
            print("\n수동으로 생성된 학생 목록:")
            for student in manual_students:
                print(f"ID: {student['id']}, 이름: {student['name']}")
            
    except Exception as e:
        print(f"오류 발생: {e}")