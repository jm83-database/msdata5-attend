  // 페이지 상단으로 스크롤
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };
  
  // 페이지 하단으로 스크롤
  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };
  
  // 학생 목록 테이블로 스크롤
  const scrollToStudentList = () => {
    const studentList = document.getElementById('student-list-table');
    if (studentList) {
      studentList.scrollIntoView({ behavior: 'smooth' });
    }
  };
    // 선택된 학생 개별 삭제 실행
  const deleteSelectedStudentsOne = async () => {
    if (selectedStudents.length === 0) return;
    
    try {
      let deletedCount = 0;
      const errors = [];
      
      // 선택된 학생을 하나씩 처리
      for (const studentId of selectedStudents) {
        console.log(`학생 ID ${studentId} 삭제 시도...`);
        
        try {
          const response = await fetch(`/api/students/${studentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ teacher_password: multiDeletePassword })
          });
          
          if (response.ok) {
            deletedCount++;
            console.log(`학생 ID ${studentId} 삭제 성공`);
          } else {
            const data = await response.json();
            errors.push(`ID ${studentId}: ${data.message || '삭제 실패'}`);
            console.error(`학생 ID ${studentId} 삭제 실패:`, data.message);
          }
        } catch (err) {
          errors.push(`ID ${studentId}: 서버 오류`);
          console.error(`학생 ID ${studentId} 삭제 중 오류:`, err);
        }
      }
      
      // 성공 시 목록 새로고침 및 선택 초기화
      fetchStudents();
      setSelectedStudents([]);
      setSelectAll(false);
      
      if (errors.length > 0) {
        setMessage(`${deletedCount}명 삭제 성공, ${errors.length}명 실패`);
      } else {
        setMessage(`${deletedCount}명의 학생이 삭제되었습니다.`);
      }
      
      closeMultiDeleteModal();
    } catch (error) {
      console.error('Error in individual delete process:', error);
      setMessage('서버 오류가 발생했습니다.');
      closeMultiDeleteModal();
    }
  };// AttendanceChecker 컴포넌트
const AttendanceChecker = () => {
  const [students, setStudents] = React.useState([]);
  const [selectedStudents, setSelectedStudents] = React.useState([]);
  const [selectAll, setSelectAll] = React.useState(false);
  const [showMultiDeleteConfirm, setShowMultiDeleteConfirm] = React.useState(false);
  const [code, setCode] = React.useState('');
  const [codeGenerationTime, setCodeGenerationTime] = React.useState(''); // 코드 생성 시간 추가
  const [codeIsValid, setCodeIsValid] = React.useState(false); // 코드 유효 상태
  const [codeIsExpired, setCodeIsExpired] = React.useState(false); // 코드 만료 상태
  const [timeRemaining, setTimeRemaining] = React.useState(0); // 남은 시간
  const [studentCode, setStudentCode] = React.useState('');
  const [studentName, setStudentName] = React.useState('');
  const [studentPassword, setStudentPassword] = React.useState('');  // 비밀번호 상태 추가
  const [confirmationMode, setConfirmationMode] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const [currentTime, setCurrentTime] = React.useState(new Date());
  
  // 출석률 관련 상태 추가
  const [attendanceRate, setAttendanceRate] = React.useState('0.0');
  const [presentCount, setPresentCount] = React.useState(0);
  const [totalCount, setTotalCount] = React.useState(0);
  
  // 선생님 권한 확인을 위한 상태 추가
  const [showTeacherModal, setShowTeacherModal] = React.useState(false);
  const [teacherPassword, setTeacherPassword] = React.useState('');
  const [pendingAction, setPendingAction] = React.useState(null); // 대기 중인 액션 (reset, downloadAttendance, downloadPasswords, generateCode)
  
  // 학생 삭제 관련 상태 추가
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  const [studentToDelete, setStudentToDelete] = React.useState(null);
  const [showDeletedStudents, setShowDeletedStudents] = React.useState(false);
  const [deletedStudents, setDeletedStudents] = React.useState([]);
  const [multiDeletePassword, setMultiDeletePassword] = React.useState('');
  
  // 학생 복구 관련 상태 추가
  const [showRestoreModal, setShowRestoreModal] = React.useState(false);
  const [pendingStudentRestore, setPendingStudentRestore] = React.useState(null);
  
  // 체크박스 선택 처리 함수
  const handleSelectStudent = (studentId) => {
    if (selectedStudents.includes(studentId)) {
      setSelectedStudents(selectedStudents.filter(id => id !== studentId));
    } else {
      setSelectedStudents([...selectedStudents, studentId]);
    }
    // 모든 학생이 선택되었는지 체크
    if (selectedStudents.length + 1 === students.length) {
      setSelectAll(true);
    } else {
      setSelectAll(false);
    }
  };

  // 전체 선택/해제 처리 함수
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedStudents([]);
    } else {
      setSelectedStudents(students.map(student => student.id));
    }
    setSelectAll(!selectAll);
  };

  // 일괄 삭제 모달 열기
  const openMultiDeleteModal = () => {
    if (selectedStudents.length === 0) {
      setMessage('삭제할 학생을 선택해주세요.');
      return;
    }
    setMultiDeletePassword('');
    setShowMultiDeleteConfirm(true);
  };

  // 일괄 삭제 모달 닫기
  const closeMultiDeleteModal = () => {
    setShowMultiDeleteConfirm(false);
    setMultiDeletePassword('');
  };

  // 선택된 학생 일괄 삭제 실행
  const deleteSelectedStudents = async () => {
    if (selectedStudents.length === 0) return;
    
    try {
      // 개별 삭제 방식으로 변경
      let deletedCount = 0;
      const errors = [];
      
      // 선택된 학생을 하나씩 처리
      for (const studentId of selectedStudents) {
        console.log(`학생 ID ${studentId} 삭제 시도...`);
        
        try {
          const response = await fetch(`/api/students/${studentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ teacher_password: multiDeletePassword })
          });
          
          if (response.ok) {
            deletedCount++;
            console.log(`학생 ID ${studentId} 삭제 성공`);
          } else {
            const data = await response.json();
            errors.push(`ID ${studentId}: ${data.message || '삭제 실패'}`);
            console.error(`학생 ID ${studentId} 삭제 실패:`, data.message);
          }
        } catch (err) {
          errors.push(`ID ${studentId}: 서버 오류`);
          console.error(`학생 ID ${studentId} 삭제 중 오류:`, err);
        }
      }
      
      // 성공 시 목록 새로고침 및 선택 초기화
      fetchStudents();
      setSelectedStudents([]);
      setSelectAll(false);
      
      if (errors.length > 0) {
        setMessage(`${deletedCount}명 삭제 성공, ${errors.length}명 실패`);
      } else {
        setMessage(`${deletedCount}명의 학생이 삭제되었습니다.`);
      }
      
      closeMultiDeleteModal();
    } catch (error) {
      console.error('Error in individual delete process:', error);
      setMessage('서버 오류가 발생했습니다.');
      closeMultiDeleteModal();
    }
  };

  // 모달이 열렸는지 확인하는 함수
  const isAnyModalOpen = () => {
    return showTeacherModal || showDeleteConfirm || showMultiDeleteConfirm || showRestoreModal || showDeletedStudents;
  };
  
  // 학생 목록 가져오기 (성능 최적화)
  const fetchStudents = React.useCallback(async () => {
    try {
      const response = await fetch('/api/students');
      const data = await response.json();
      
      // 데이터를 정렬
      const sortedStudents = data.sort((a, b) => a.id - b.id);
      
      // 상태 업데이트 (React가 자동으로 변경 감지)
      setStudents(sortedStudents);
      
      // 출석률 계산
      const totalStudents = sortedStudents.length;
      const presentStudents = sortedStudents.filter(student => student.present === true).length;
      const rate = totalStudents > 0 ? (presentStudents / totalStudents) * 100 : 0;
      
      console.log(`출석률 계산: ${presentStudents}/${totalStudents} = ${rate.toFixed(1)}%`); // 디버깅용
      
      setTotalCount(totalStudents);
      setPresentCount(presentStudents);
      setAttendanceRate(rate.toFixed(1));
      
      console.log('상태 업데이트 완료:', {
        totalCount: totalStudents,
        presentCount: presentStudents,
        attendanceRate: rate.toFixed(1)
      });
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  }, []); // dependency 배열에서 students 제거
  
  // 출석 코드 가져오기 (성능 최적화)
  const fetchCode = React.useCallback(async () => {
    try {
      const response = await fetch('/api/code');
      const data = await response.json();
      
      console.log('코드 데이터 받음:', data); // 디버깅용
      
      // 상태 업데이트 (React가 자동으로 변경 감지)
      setCode(data.code || '');
      setCodeGenerationTime(data.generationTime || '');
      setCodeIsValid(data.isValid || false);
      setCodeIsExpired(data.isExpired || false);
      setTimeRemaining(data.timeRemaining || 0);
    } catch (error) {
      console.error('Failed to fetch code:', error);
      // 에러 시 기본값으로 초기화
      setCode('');
      setCodeGenerationTime('');
      setCodeIsValid(false);
      setCodeIsExpired(false);
      setTimeRemaining(0);
    }
  }, []); // dependency 배열 비우기
  
  // 새 출석 코드 생성하기 (선생님 비밀번호 필요)
  const generateNewCode = async () => {
    try {
      const response = await fetch('/api/code/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          teacher_password: teacherPassword
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 코드 생성 성공 시 모든 관련 상태 업데이트
        setCode(data.code);
        setCodeGenerationTime(data.generationTime || '');
        setCodeIsValid(true); // 새로 생성된 코드는 유효함
        setCodeIsExpired(false); // 만료되지 않음
        setTimeRemaining(300); // 5분 (300초) 유효
        setMessage('새 출석 코드가 생성되었습니다.');
        
        // 즉시 코드 상태를 다시 가져와서 동기화
        setTimeout(() => {
          fetchCode();
        }, 100);
      } else {
        setMessage(data.message || '코드 생성 실패');
      }
    } catch (error) {
      console.error('Failed to generate code:', error);
      setMessage('서버 오류가 발생했습니다.');
    }
  };
  
  // 초기 데이터 로드 및 타이머 설정
  // 한국 시간 표시를 위한 함수
  const getKoreanTime = () => {
    const now = new Date();
    // 한국 시간은 UTC+9
    return now;
  };

  // 코드 유효 상태가 변경될 때 학생 목록 인터벌을 관리하기 위한 인터벌 참조 상태
  const studentsIntervalRef = React.useRef(null);

  // 학생 목록 갱신 인터벌 설정/해제 함수 (최적화)
  const manageStudentsInterval = React.useCallback((isCodeValid) => {
    // 기존 인터벌이 있으면 제거
    if (studentsIntervalRef.current) {
      clearInterval(studentsIntervalRef.current);
      studentsIntervalRef.current = null;
    }
    
    // 코드가 유효한 경우에만 인터벌 설정 (주기 15초로 연장)
    if (isCodeValid) {
      studentsIntervalRef.current = setInterval(fetchStudents, 15000);
    } else {
      // 코드가 유효하지 않을 때는 한 번만 학생 목록 갱신
      fetchStudents();
    }
  }, [fetchStudents]);

  // 코드 상태가 변경될 때 학생 목록 인터벌 관리
  React.useEffect(() => {
    manageStudentsInterval(codeIsValid);
    
    return () => {
      if (studentsIntervalRef.current) {
        clearInterval(studentsIntervalRef.current);
      }
    };
  }, [codeIsValid]);

  React.useEffect(() => {
    console.log('컴포넌트 초기화 시작');
    
    // 초기 데이터 로드
    fetchStudents();
    
    // 약간의 지연을 두고 코드 상태 체크 (동시 요청 방지)
    setTimeout(() => {
      fetchCode();
    }, 100);
    
    // 시간 업데이트는 1초마다, 코드 상태는 3초마다 체크 (성능 최적화)
    const timeInterval = setInterval(() => {
      setCurrentTime(getKoreanTime());
    }, 1000);
    
    const codeInterval = setInterval(() => {
      console.log('정기적 코드 상태 체크');
      fetchCode();
    }, 10000); // 10초마다 코드 상태 체크
    
    return () => {
      clearInterval(timeInterval);
      clearInterval(codeInterval);
      if (studentsIntervalRef.current) {
        clearInterval(studentsIntervalRef.current);
      }
    };
  }, []);
  
  // 출석 확인 처리
  const handleConfirmAttendance = async () => {
    if (!studentName.trim()) {
      setMessage('이름을 입력해주세요.');
      return;
    }
    
    if (!studentCode.trim()) {
      setMessage('출석 코드를 입력해주세요.');
      return;
    }
    
    if (!studentPassword.trim()) {
      setMessage('비밀번호를 입력해주세요.');
      return;
    }
    
    try {
      const response = await fetch('/api/attendance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: studentName,
          code: studentCode,
          password: studentPassword  // 비밀번호 추가
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 성공 시 입력 필드 초기화
        setStudentName('');
        setStudentCode('');
        setStudentPassword('');  // 비밀번호 초기화
        
        // 성공 메시지 표시
        setMessage(`${data.message} \n출석이 성공적으로 등록되었습니다.`);
      } else {
        setMessage(data.message || '출석 확인 실패');
      }
    } catch (error) {
      console.error('Error confirming attendance:', error);
      setMessage('서버 오류가 발생했습니다.');
    }
  };
  
  // 선생님 권한 확인 모달 열기
  const openTeacherModal = (action) => {
    setPendingAction(action);
    setTeacherPassword('');
    setShowTeacherModal(true);
  };
  
  // 선생님 권한 확인 모달 닫기
  const closeTeacherModal = () => {
    setShowTeacherModal(false);
    setPendingAction(null);
    setTeacherPassword('');
  };
  
  // 선생님 비밀번호 확인
  const verifyTeacherPassword = () => {
    if (teacherPassword !== 'teacher') {
      setMessage('선생님 비밀번호가 올바르지 않습니다.');
      closeTeacherModal();
      return false;
    }
    closeTeacherModal();
    return true;
  };
  
  // 선생님 비밀번호 검증 후 액션 실행
  const executeTeacherAction = async () => {
    if (!verifyTeacherPassword()) {
      return;
    }
    
    switch (pendingAction) {
      case 'reset':
        await resetAttendanceExecute();
        break;
      case 'downloadAttendance':
        downloadAttendanceCSVExecute();
        break;
      case 'downloadPasswords':
        downloadStudentPasswordsExecute();
        break;
      case 'viewDeletedStudents':
        fetchDeletedStudents();
        break;
      case 'generateCode':
        generateNewCode();
        break;
    }
  };
  
  // 학생 삭제 모달 열기
  const openDeleteModal = (student) => {
    setStudentToDelete(student);
    setShowDeleteConfirm(true);
  };

  // 학생 삭제 모달 닫기
  const closeDeleteModal = () => {
    setShowDeleteConfirm(false);
    setStudentToDelete(null);
    setTeacherPassword('');
  };

  // 학생 삭제 실행
  const deleteStudent = async () => {
    if (!studentToDelete) return;
    
    try {
      const response = await fetch(`/api/students/${studentToDelete.id}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teacher_password: teacherPassword })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        fetchStudents(); // 학생 목록 새로고침
        setMessage(data.message);
      } else {
        setMessage(data.message);
      }
      
      closeDeleteModal();
    } catch (error) {
      console.error('Error deleting student:', error);
      setMessage('서버 오류가 발생했습니다.');
      closeDeleteModal();
    }
  };

  // 삭제된 학생 목록 불러오기
  const fetchDeletedStudents = async () => {
    try {
      console.log(`삭제된 학생 목록 조회 시도: 교사 비밀번호 길이=${teacherPassword.length}`);
      
      const response = await fetch(`/api/students/deleted?teacher_password=${teacherPassword}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log('삭제된 학생 목록:', data);
        
        // ID 기준으로 삭제된 학생 목록 정렬
        const sortedDeletedStudents = [...data].sort((a, b) => a.id - b.id);
        setDeletedStudents(sortedDeletedStudents);
        
        setShowDeletedStudents(true);
      } else {
        const data = await response.json();
        console.error('삭제된 학생 목록 조회 실패:', data);
        setMessage(data.message || '삭제된 학생 조회 실패');
      }
    } catch (error) {
      console.error('Error fetching deleted students:', error);
      setMessage('서버 오류가 발생했습니다. 개발자 콘솔을 확인하세요.');
    }
  };

  // 학생 복구 모달 열기 (수정된 부분)
  const restoreStudent = (studentId) => {
    // 복구할 학생 ID 저장
    setPendingStudentRestore(studentId);
    
    // 비밀번호 초기화 및 모달 표시
    setTeacherPassword('');
    
    // 먼저 삭제된 학생 목록 모달을 닫고 바로 복구 모달 표시
    setShowDeletedStudents(false);
    setShowRestoreModal(true);
  };

  // 학생 복구 실행 (수정된 부분)
  const executeRestore = async () => {
    if (!pendingStudentRestore) return;
    
    try {
      console.log(`복구 시도: 학생 ID=${pendingStudentRestore}, 교사 비밀번호 길이=${teacherPassword.length}`);
      
      const response = await fetch('/api/students/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: pendingStudentRestore,
          teacher_password: teacherPassword
        })
      });
      
      const data = await response.json();
      console.log('복구 응답:', data);
      
      if (response.ok) {
        // 학생 목록 새로고침
        fetchStudents();
        
        // 모달 닫기 및 초기화
        setShowRestoreModal(false);
        setPendingStudentRestore(null);
        
        // 성공 메시지 표시 - 팝업 효과를 주기 위해 사용자 인터페이스에 명확하게 표시
        setMessage(data.message);
      } else {
        setMessage(data.message || '복구 실패: 서버 응답 오류');
        setShowRestoreModal(false);
        setPendingStudentRestore(null);
      }
      
    } catch (error) {
      console.error('Error restoring student:', error);
      setMessage('서버 오류가 발생했습니다. 개발자 콘솔을 확인하세요.');
      setShowRestoreModal(false);
      setPendingStudentRestore(null);
    }
  };

  // 복구 모달 닫기
  const closeRestoreModal = () => {
    setShowRestoreModal(false);
    setPendingStudentRestore(null);
    setTeacherPassword('');
  };

  // 삭제된 학생 목록 모달 닫기
  const closeDeletedStudentsModal = () => {
    setShowDeletedStudents(false);
  };
  
  // 출석부 초기화 요청
  const resetAttendance = () => {
    openTeacherModal('reset');
  };
  
  // 출석부 초기화 실행
  const resetAttendanceExecute = async () => {
    try {
      const response = await fetch('/api/attendance/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        fetchStudents(); // 학생 목록 새로고침
      }
      
      setMessage(data.message);
    } catch (error) {
      console.error('Error resetting attendance:', error);
      setMessage('서버 오류가 발생했습니다.');
    }
  };
  
  // 출석부 CSV 다운로드 요청
  const downloadAttendanceCSV = () => {
    openTeacherModal('downloadAttendance');
  };
  
  // 출석부 CSV 다운로드 실행
  const downloadAttendanceCSVExecute = () => {
    window.location.href = '/api/attendance/download';
  };
  
  // 학생 비밀번호 CSV 다운로드 요청 (선생님용)
  const downloadStudentPasswords = () => {
    openTeacherModal('downloadPasswords');
  };
  
  // 학생 비밀번호 CSV 다운로드 실행
  const downloadStudentPasswordsExecute = () => {
    window.location.href = '/api/students/passwords';
  };
  
  // 모드 전환
  const toggleMode = () => {
    setConfirmationMode(!confirmationMode);
    setMessage('');
    setStudentName('');
    setStudentCode('');
    setStudentPassword('');
  };
  
  return (
    <div className="w-full max-w-4xl mx-auto p-2 sm:p-4">
      {/* 선생님 비밀번호 확인 모달 */}
      {showTeacherModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">선생님 인증</h3>
            <p className="text-sm text-gray-600 mb-4">선생님 비밀번호를 입력해주세요.</p>
            <input
              type="password"
              value={teacherPassword}
              onChange={e => setTeacherPassword(e.target.value)}
              placeholder="선생님 비밀번호"
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={closeTeacherModal}
                className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
              >
                취소
              </button>
              <button
                onClick={executeTeacherAction}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 학생 삭제 확인 모달 */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">학생 삭제 확인</h3>
            <p className="text-sm text-gray-600 mb-4">
              <strong>{studentToDelete && studentToDelete.name}</strong> 학생을 삭제하시겠습니까?
              <br />이 작업은 되돌릴 수 있지만, 출석 기록은 초기화됩니다.
            </p>
            <input
              type="password"
              value={teacherPassword}
              onChange={e => setTeacherPassword(e.target.value)}
              placeholder="선생님 비밀번호"
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={closeDeleteModal}
                className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
              >
                취소
              </button>
              <button
                onClick={deleteStudent}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 학생 일괄 삭제 확인 모달 */}
      {showMultiDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">학생 일괄 삭제 확인</h3>
            <p className="text-sm text-gray-600 mb-4">
              <strong>{selectedStudents.length}명</strong>의 학생을 삭제하시겠습니까?
              <br />이 작업은 되돌릴 수 있지만, 출석 기록은 초기화됩니다.
            </p>
            <input
              type="password"
              value={multiDeletePassword}
              onChange={e => setMultiDeletePassword(e.target.value)}
              placeholder="선생님 비밀번호"
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={closeMultiDeleteModal}
                className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
              >
                취소
              </button>
              <button
                onClick={deleteSelectedStudents}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                일괄 삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 학생 복구 확인 모달 (새로 추가) */}
      {showRestoreModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">학생 복구 확인</h3>
            <p className="text-sm text-gray-600 mb-4">
              학생을 복구하려면 선생님 비밀번호를 입력하세요.
            </p>
            <input
              type="password"
              value={teacherPassword}
              onChange={e => setTeacherPassword(e.target.value)}
              placeholder="선생님 비밀번호"
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={closeRestoreModal}
                className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
              >
                취소
              </button>
              <button
                onClick={executeRestore}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                복구
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 삭제된 학생 목록 모달 */}
      {showDeletedStudents && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-2xl">
            <h3 className="text-lg font-medium mb-4">삭제된 학생 목록</h3>
            
            {deletedStudents.length === 0 ? (
              <p className="text-gray-600">삭제된 학생이 없습니다.</p>
            ) : (
              <div className="h-64 overflow-y-auto border border-gray-200 rounded mb-4">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0 z-10">
                    <tr>
                      <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">ID</th>
                      <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">이름</th>
                      <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">삭제 시간</th>
                      <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">작업</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {deletedStudents.map(student => (
                      <tr key={student.id}>
                        <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-center">{student.id}</td>
                        <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-center">{student.name}</td>
                        <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                          {student.deleted_at || '-'}
                        </td>
                        <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-center">
                          <button
                            onClick={() => restoreStudent(student.id)}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            복구
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            <div className="flex justify-end">
              <button
                onClick={closeDeletedStudentsModal}
                className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md overflow-hidden max-w-full">
        {/* 플로팅 퀴 메뉴 */}
        <div className="fixed right-4 bottom-4 flex flex-col gap-2 z-20">
          <button 
            onClick={scrollToTop}
            className="w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-indigo-700 transition-colors"
            title="상단으로 이동"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </button>
          
          <button 
            onClick={scrollToBottom}
            className="w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-indigo-700 transition-colors"
            title="하단으로 이동"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>
        </div>
        {/* 고정 헤더 영역 (학생 모드에서는 표시 안함, 모달 열렸을 때도 숨김) */}
        {!confirmationMode && !isAnyModalOpen() && (
          <div className="fixed left-0 right-0 top-0 z-50 bg-white shadow-lg border-b border-gray-200">
            <div className="max-w-4xl mx-auto p-3">
              {/* 헤더 상단 */}
              <div className="flex justify-between items-center mb-3">
                <div className="text-sm flex items-center gap-2">
                  <span className="inline-block w-4 h-4">⏰</span>
                  {currentTime.toLocaleTimeString()}
                </div>
                <button
                  onClick={toggleMode}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors shadow-md"
                >
                  학생 모드로 전환
                </button>
              </div>
              
              {/* 시스템 타이틀 */}
              <div className="text-center mb-3">
                <h2 className="text-xl font-bold text-indigo-800">온라인 수업 출석 확인 시스템</h2>
                <p className="text-xs text-indigo-600 mt-1 font-medium inline-block px-3 py-1 bg-indigo-100 rounded-full">
                  선생님 관리 모드
                </p>
              </div>
              
              {/* 출석 카드 영역 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-4 mb-3">
                {/* 출석 코드 카드 */}
                <div className="p-3 rounded-lg shadow-md text-center text-white" style={{
                  background: codeIsValid ? 'linear-gradient(to right, #3B82F6, #1D4ED8)' : 
                             codeIsExpired ? 'linear-gradient(to right, #EF4444, #DC2626)' : 
                             'linear-gradient(to right, #6B7280, #4B5563)',
                  backgroundColor: codeIsValid ? '#3B82F6' : codeIsExpired ? '#EF4444' : '#6B7280'
                }}>
                  <div className="text-xs font-medium">수업 출석 코드</div>
                  <div className="text-2xl font-bold tracking-wider">{code && code !== '' ? code : '없음'}</div>
                  <div className="mt-1 text-xs font-medium">
                    {code && codeIsValid && timeRemaining > 0 && (
                      <span className="inline-block px-2 py-0.5 bg-green-600 rounded-full text-xs">
                        유효: {Math.floor(timeRemaining / 60)}분 {timeRemaining % 60}초 남음
                      </span>
                    )}
                    {code && (codeIsExpired || timeRemaining <= 0) && (
                      <span className="inline-block px-2 py-0.5 bg-red-600 rounded-full text-xs">
                        만료됨
                      </span>
                    )}
                    {(!code || code === '') && (
                      <span className="inline-block px-2 py-0.5 bg-gray-600 rounded-full text-xs">
                        코드를 생성해주세요
                      </span>
                    )}
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <div className="text-xs text-blue-100">
                      {codeGenerationTime ? `생성: ${codeGenerationTime}` : ''}
                    </div>
                    <button 
                      onClick={() => openTeacherModal('generateCode')}
                      className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 shadow-sm"
                    >
                      코드 생성
                    </button>
                  </div>
                </div>
                
                {/* 출석률 카드 */}
                <div className="p-3 rounded-lg shadow-md" style={{
                  background: 'linear-gradient(to right, #10B981, #047857)',
                  backgroundColor: '#10B981'
                }}>
                  <div className="flex justify-between items-center text-white">
                    <div className="text-xs font-medium">현재 출석률</div>
                    <div className="text-sm font-bold">{presentCount}/{totalCount}명 ({totalCount > 0 ? attendanceRate : 0}%)</div>
                  </div>
                  <div className="w-full bg-white bg-opacity-30 rounded-full h-3 mt-2">
                    <div 
                      className="bg-white h-3 rounded-full" 
                      style={{ width: `${attendanceRate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              
              {/* 학생 목록 헤더 */}
              <div className="relative mb-3 pb-2 border-b">
                <h3 className="text-lg font-medium text-center">
                  학생 목록
                </h3>
                {selectedStudents.length > 0 && (
                  <button
                    onClick={openMultiDeleteModal}
                    className="absolute right-0 top-0 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 flex-shrink-0"
                  >
                    {selectedStudents.length}명 삭제
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* 학생 모드일 때 표시되는 일반 헤더 - 모달 열렸을 때는 숨김 */}
        {confirmationMode && !isAnyModalOpen() && (
          <div className="p-4 border-b">
            <div className="flex justify-between items-center mb-3">
              <div className="text-sm flex items-center gap-2">
                <span className="inline-block w-4 h-4">⏰</span>
                {currentTime.toLocaleTimeString()}
              </div>
              <button
                onClick={toggleMode}
                className="px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors shadow-md"
              >
                선생님 모드로 전환
              </button>
            </div>
            
            <div className="text-center">
              <h2 className="text-2xl font-bold text-indigo-800">온라인 수업 출석 확인 시스템</h2>
              <p className="text-sm text-indigo-600 mt-1 font-medium inline-block px-3 py-1 bg-indigo-100 rounded-full">
                학생 출석 확인 모드
              </p>
            </div>
          </div>
        )}
        
        <div className="p-4">
          {confirmationMode ? (
            <div className="space-y-4">
              {/* 유효한 코드가 없을 때 알림 표시 */}
              {(!codeIsValid && code) && (
                <div className="bg-red-100 text-red-800 p-3 rounded-lg text-center font-medium mb-4">
                  출석 코드가 만료되었습니다. 선생님에게 새 코드를 요청하세요.
                </div>
              )}
              {codeIsValid && (
                <div className="bg-green-100 text-green-800 p-3 rounded-lg text-center font-medium mb-4">
                  현재 코드: <span className="font-bold">{code}</span>
                  <div className="text-xs mt-1">
                    유효시간: {Math.floor(timeRemaining / 60)}분 {timeRemaining % 60}초 남음
                  </div>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium mb-1">이름</label>
                <input
                  type="text"
                  value={studentName}
                  onChange={e => setStudentName(e.target.value)}
                  placeholder="이름을 입력하세요"
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">출석 코드</label>
                <input
                  type="text"
                  value={studentCode}
                  onChange={e => setStudentCode(e.target.value)}
                  placeholder="선생님이 제공한 코드를 입력하세요"
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">개인 비밀번호</label>
                <input
                  type="password"
                  value={studentPassword}
                  onChange={e => setStudentPassword(e.target.value)}
                  placeholder="개인 비밀번호를 입력하세요"
                  className="w-full p-2 border rounded"
                />
              </div>
              <button 
                onClick={handleConfirmAttendance}
                className="w-full mt-4 bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
                disabled={!codeIsValid}
              >
                출석 확인
              </button>
              {message && (
                <div className={`mt-2 p-3 rounded text-center ${message.includes('성공') || message.includes('확인') ? 'bg-green-100 text-green-800 font-medium' : 'bg-red-100 text-red-800'}`}>
                  {message.split('\n').map((line, index) => (
                    <p key={index}>{line}</p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {/* 헤더 높이를 맞춤으로 내용이 가려지지 않도록 하는 여백 - 모달 열렸을 때는 여백 낮게 조정 */}
              <div className={`${isAnyModalOpen() ? 'h-10' : 'h-80 md:h-72'}`}></div>
              
              <div className="mt-3">
                
                <div className="border rounded-lg overflow-x-auto shadow">
                  <table id="student-list-table" className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 sm:px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <input
                            type="checkbox"
                            checked={selectAll}
                            onChange={handleSelectAll}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                          />
                        </th>
                        <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                        <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">출석 상태</th>
                        <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">확인 시간</th>
                        <th className="px-3 sm:px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">관리</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {students.map(student => (
                        <tr key={student.id} className={student.present ? "bg-green-50" : ""}>
                          <td className="px-2 sm:px-3 py-2 sm:py-4 whitespace-nowrap text-center">
                            <input
                              type="checkbox"
                              checked={selectedStudents.includes(student.id)}
                              onChange={() => handleSelectStudent(student.id)}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap font-medium text-center">{student.name}</td>
                          <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-center">
                            <span className={`inline-flex px-2 py-1 text-xs rounded-full ${student.present ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {student.present ? '출석' : '미출석'}
                            </span>
                          </td>
                          <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-sm text-gray-500 text-center">
                            {student.timestamp || '-'}
                          </td>
                          <td className="px-3 sm:px-6 py-2 sm:py-4 whitespace-nowrap text-center">
                            <button
                              onClick={() => openDeleteModal(student)}
                              className="text-red-600 hover:text-red-800 text-sm hover:underline"
                            >
                              삭제
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="mt-8">
                <h3 className="text-lg font-medium mb-4 text-center">관리 기능</h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
                  <button
                    onClick={resetAttendance}
                    className="flex flex-col items-center justify-center p-2 sm:p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-red-50 hover:border-red-200 transition-all"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span className="text-xs sm:text-sm font-medium">출석부 초기화</span>
                  </button>
                  
                  <button
                    onClick={downloadAttendanceCSV}
                    className="flex flex-col items-center justify-center p-2 sm:p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-green-50 hover:border-green-200 transition-all"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span className="text-xs sm:text-sm font-medium">출석부 다운로드</span>
                  </button>
                  
                  <button
                    onClick={downloadStudentPasswords}
                    className="flex flex-col items-center justify-center p-2 sm:p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-yellow-50 hover:border-yellow-200 transition-all"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span className="text-xs sm:text-sm font-medium">비밀번호 다운로드</span>
                  </button>
                  
                  <button
                    onClick={() => { openTeacherModal('viewDeletedStudents'); }}
                    className="flex flex-col items-center justify-center p-2 sm:p-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-purple-50 hover:border-purple-200 transition-all"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <span className="text-xs sm:text-sm font-medium">삭제된 학생</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* 하단 모드 전환 버튼 제거 */}
      </div>
    </div>
  );
};

// 앱 렌더링
ReactDOM.render(
  <AttendanceChecker />,
  document.getElementById('app')
);