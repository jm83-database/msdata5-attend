"""
Azure Cosmos DB Service for Attendance System
Handles all database operations with JSON fallback for local development
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional
from threading import RLock

# Try to import Cosmos DB SDK, fallback to local JSON if not available
try:
    from azure.cosmos import CosmosClient, PartitionKey
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False
    print("Warning: azure-cosmos not installed. Using local JSON fallback.")


class CosmosService:
    """
    Unified data access layer for attendance management.
    Uses Azure Cosmos DB when available, falls back to JSON files.
    """

    def __init__(self, cohort_id: str = None):
        """
        Initialize Cosmos DB service.

        Args:
            cohort_id: Cohort identifier (e.g., 'AI10', 'AI9', 'DT3', 'DT4')
                      If None, uses COHORT_ID environment variable
        """
        self.cohort_id = cohort_id or os.environ.get('COHORT_ID', 'AI10')
        self.data_lock = RLock()
        self.use_cosmos = False
        self.client = None
        self.container = None

        # Initialize Cosmos DB connection if credentials available
        if COSMOS_AVAILABLE and self._has_cosmos_credentials():
            try:
                self._init_cosmos_db()
                self.use_cosmos = True
                print(f"Cosmos DB initialized for cohort: {self.cohort_id}")
            except Exception as e:
                print(f"Failed to initialize Cosmos DB: {e}. Falling back to JSON storage.")
                self.use_cosmos = False

        # Local JSON file paths (for fallback)
        self.students_file = 'students.json'
        self.attendance_file = 'attendance.json'
        self.deleted_students_file = 'logs/deleted_students.json'

        # Cosmos DB가 연결됐는데 데이터가 없으면 로컬 JSON에서 자동 마이그레이션
        if self.use_cosmos:
            self._migrate_from_json_if_needed()

    def _has_cosmos_credentials(self) -> bool:
        """Check if Cosmos DB credentials are available in environment."""
        return all([
            os.environ.get('COSMOS_ENDPOINT'),
            os.environ.get('COSMOS_KEY'),
            os.environ.get('COSMOS_DB'),
            os.environ.get('COSMOS_CONTAINER')
        ])

    def _init_cosmos_db(self):
        """Initialize Cosmos DB client and container."""
        endpoint = os.environ.get('COSMOS_ENDPOINT')
        key = os.environ.get('COSMOS_KEY')
        db_name = os.environ.get('COSMOS_DB')
        container_name = os.environ.get('COSMOS_CONTAINER')

        self.client = CosmosClient(endpoint, credential=key)
        database = self.client.get_database_client(db_name)
        self.container = database.get_container_client(container_name)

    def _migrate_from_json_if_needed(self):
        """로컬 JSON에서 Cosmos DB로 초기 데이터 마이그레이션 (최초 1회)."""
        existing = self._load_students_cosmos()
        if existing:
            return

        students_file = 'students.json'
        if os.path.exists(students_file):
            try:
                with open(students_file, 'r', encoding='utf-8') as f:
                    students = json.load(f)
                if students:
                    self._save_students_cosmos(students)
                    print(f"[Migration] students.json → Cosmos DB ({self.cohort_id}) 마이그레이션 완료: {len(students)}명")
            except Exception as e:
                print(f"[Migration] 마이그레이션 실패: {e}")

    # ========== STUDENTS OPERATIONS ==========

    def load_students(self) -> List[Dict[str, Any]]:
        """Load all students for this cohort."""
        if self.use_cosmos:
            return self._load_students_cosmos()
        else:
            return self._load_students_json()

    def _load_students_cosmos(self) -> List[Dict[str, Any]]:
        """Load students from Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_students"
            doc = self.container.read_item(item=doc_id, partition_key=self.cohort_id)
            return doc.get('data', [])
        except Exception as e:
            print(f"Error loading students from Cosmos DB: {e}")
            # Return empty list if document doesn't exist yet
            return []

    def _load_students_json(self) -> List[Dict[str, Any]]:
        """Load students from local JSON file."""
        try:
            if os.path.exists(self.students_file):
                with open(self.students_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading students from JSON: {e}")
            return []

    def save_students(self, students: List[Dict[str, Any]]) -> bool:
        """Save all students for this cohort."""
        if self.use_cosmos:
            return self._save_students_cosmos(students)
        else:
            return self._save_students_json(students)

    def _save_students_cosmos(self, students: List[Dict[str, Any]]) -> bool:
        """Save students to Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_students"
            doc = {
                "id": doc_id,
                "cohort_id": self.cohort_id,
                "type": "students",
                "data": students,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }

            try:
                # Try to update existing document
                self.container.replace_item(item=doc_id, body=doc)
            except Exception:
                # If not found, create new document
                self.container.create_item(body=doc)

            return True
        except Exception as e:
            print(f"Error saving students to Cosmos DB: {e}")
            return False

    def _save_students_json(self, students: List[Dict[str, Any]]) -> bool:
        """Save students to local JSON file."""
        try:
            with self.data_lock:
                with open(self.students_file, 'w', encoding='utf-8') as f:
                    json.dump(students, f, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving students to JSON: {e}")
            return False

    # ========== ATTENDANCE OPERATIONS ==========

    def load_attendance(self) -> List[Dict[str, Any]]:
        """Load all attendance records for this cohort."""
        if self.use_cosmos:
            return self._load_attendance_cosmos()
        else:
            return self._load_attendance_json()

    def _load_attendance_cosmos(self) -> List[Dict[str, Any]]:
        """Load attendance records from Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_attendance"
            doc = self.container.read_item(item=doc_id, partition_key=self.cohort_id)
            return doc.get('records', [])
        except Exception as e:
            print(f"Error loading attendance from Cosmos DB: {e}")
            return []

    def _load_attendance_json(self) -> List[Dict[str, Any]]:
        """Load attendance records from local JSON file."""
        try:
            if os.path.exists(self.attendance_file):
                with open(self.attendance_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading attendance from JSON: {e}")
            return []

    def save_attendance(self, attendance_records: List[Dict[str, Any]]) -> bool:
        """Save all attendance records for this cohort."""
        if self.use_cosmos:
            return self._save_attendance_cosmos(attendance_records)
        else:
            return self._save_attendance_json(attendance_records)

    def _save_attendance_cosmos(self, records: List[Dict[str, Any]]) -> bool:
        """Save attendance records to Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_attendance"
            doc = {
                "id": doc_id,
                "cohort_id": self.cohort_id,
                "type": "attendance",
                "records": records,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }

            try:
                self.container.replace_item(item=doc_id, body=doc)
            except Exception:
                self.container.create_item(body=doc)

            return True
        except Exception as e:
            print(f"Error saving attendance to Cosmos DB: {e}")
            return False

    def _save_attendance_json(self, records: List[Dict[str, Any]]) -> bool:
        """Save attendance records to local JSON file."""
        try:
            with self.data_lock:
                with open(self.attendance_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving attendance to JSON: {e}")
            return False

    # ========== DELETED STUDENTS OPERATIONS ==========

    def load_deleted_students(self) -> List[Dict[str, Any]]:
        """Load all deleted students for this cohort."""
        if self.use_cosmos:
            return self._load_deleted_students_cosmos()
        else:
            return self._load_deleted_students_json()

    def _load_deleted_students_cosmos(self) -> List[Dict[str, Any]]:
        """Load deleted students from Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_deleted_students"
            doc = self.container.read_item(item=doc_id, partition_key=self.cohort_id)
            return doc.get('data', [])
        except Exception as e:
            print(f"Error loading deleted students from Cosmos DB: {e}")
            return []

    def _load_deleted_students_json(self) -> List[Dict[str, Any]]:
        """Load deleted students from local JSON file."""
        try:
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, 'deleted_students.json')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading deleted students from JSON: {e}")
            return []

    def save_deleted_students(self, deleted_students: List[Dict[str, Any]]) -> bool:
        """Save deleted students for this cohort."""
        if self.use_cosmos:
            return self._save_deleted_students_cosmos(deleted_students)
        else:
            return self._save_deleted_students_json(deleted_students)

    def _save_deleted_students_cosmos(self, deleted_students: List[Dict[str, Any]]) -> bool:
        """Save deleted students to Cosmos DB."""
        try:
            doc_id = f"{self.cohort_id}_deleted_students"
            doc = {
                "id": doc_id,
                "cohort_id": self.cohort_id,
                "type": "deleted_students",
                "data": deleted_students,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }

            try:
                self.container.replace_item(item=doc_id, body=doc)
            except Exception:
                self.container.create_item(body=doc)

            return True
        except Exception as e:
            print(f"Error saving deleted students to Cosmos DB: {e}")
            return False

    def _save_deleted_students_json(self, deleted_students: List[Dict[str, Any]]) -> bool:
        """Save deleted students to local JSON file."""
        try:
            with self.data_lock:
                log_dir = 'logs'
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)

                log_file = os.path.join(log_dir, 'deleted_students.json')
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(deleted_students, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving deleted students to JSON: {e}")
            return False

    def add_deleted_student(self, student: Dict[str, Any]) -> bool:
        """Add a student to the deleted students list."""
        deleted_students = self.load_deleted_students()

        # Add deletion timestamp (UTC+9 Korea time)
        student['deleted_at'] = (
            datetime.datetime.now() + datetime.timedelta(hours=9)
        ).strftime("%Y-%m-%d %H:%M:%S")

        deleted_students.append(student)
        return self.save_deleted_students(deleted_students)
