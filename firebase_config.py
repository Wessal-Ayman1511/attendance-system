"""
Firebase configuration and utility functions for the Smart Attendance System.
This module handles all Firebase operations including attendance records, 
session management, and student data storage.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Any

class FirebaseManager:
    def __init__(self, service_account_path: str = "serviceAccountKey.json"):
        """
        Initialize Firebase Admin SDK.
        
        Args:
            service_account_path: Path to the Firebase service account key JSON file
        """
        self.db = None
        self.initialize_firebase(service_account_path)
    
    def initialize_firebase(self, service_account_path: str):
        """Initialize Firebase Admin SDK with service account credentials."""
        try:
            if not firebase_admin._apps:
                if os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # Try to use default credentials (for production)
                    firebase_admin.initialize_app()
                
                self.db = firestore.client()
                print("✅ Firebase Admin SDK initialized successfully.")
            else:
                self.db = firestore.client()
                print("✅ Firebase Admin SDK already initialized.")
                
        except Exception as e:
            print(f"❌ Error initializing Firebase Admin SDK: {e}")
            raise e
    
    def save_attendance_record(self, class_id: str, student_id: str, 
                             status: str = "present", additional_data: Dict = None) -> bool:
        """
        Save attendance record to Firebase.
        
        Args:
            class_id: ID of the class
            student_id: ID of the student
            status: Attendance status (present/absent)
            additional_data: Additional data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            record_id = f"{class_id}_{student_id}_{today_str}"
            
            attendance_data = {
                'classId': class_id,
                'studentId': student_id,
                'date': today_str,
                'status': status,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'createdAt': datetime.now().isoformat()
            }
            
            if additional_data:
                attendance_data.update(additional_data)
            
            self.db.collection('attendance').document(record_id).set(attendance_data, merge=True)
            print(f"✅ Attendance record saved: {record_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving attendance record: {e}")
            return False
    
    def get_attendance_for_class(self, class_id: str, date: str = None) -> List[Dict]:
        """
        Get attendance records for a specific class.
        
        Args:
            class_id: ID of the class
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of attendance records
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            query = self.db.collection('attendance').where('classId', '==', class_id).where('date', '==', date)
            docs = query.stream()
            
            records = []
            for doc in docs:
                record = doc.to_dict()
                record['id'] = doc.id
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"❌ Error getting attendance records: {e}")
            return []
    
    def save_session_data(self, session_id: str, session_name: str, 
                         start_time: datetime, end_time: datetime, 
                         duration_minutes: int, recognized_students: List[str],
                         class_id: str = None) -> bool:
        """
        Save session data to Firebase.
        
        Args:
            session_id: Unique session identifier
            session_name: Name of the session
            start_time: Session start time
            end_time: Session end time
            duration_minutes: Duration in minutes
            recognized_students: List of recognized student IDs
            class_id: Optional class identifier for integration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session_data = {
                'sessionId': session_id,
                'sessionName': session_name,
                'startTime': start_time,
                'endTime': end_time,
                'durationMinutes': duration_minutes,
                'recognizedStudents': recognized_students,
                'totalStudents': len(recognized_students),
                'createdAt': firestore.SERVER_TIMESTAMP,
                # New fields for transcript/summary/quiz integration
                'audioProcessed': False,
                'processingStatus': 'pending'
            }
            
            if class_id:
                session_data['classId'] = class_id
            
            self.db.collection('sessions').document(session_id).set(session_data, merge=True)
            print(f"✅ Session data saved: {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving session data: {e}")
            return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            doc = self.db.collection('sessions').document(session_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            print(f"❌ Error getting session data: {e}")
            return None
    
    def get_attendance_for_session(self, session_id: str) -> List[Dict]:
        """
        Get attendance records for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of attendance records for that session
        """
        try:
            # First get the session data
            session = self.get_session_data(session_id)
            if not session:
                return []
            
            class_id = session.get('classId')
            start_time = session.get('startTime')
            
            # Extract date from startTime
            if start_time:
                from datetime import datetime
                from firebase_admin import firestore as firestore_module
                
                # Handle Firestore Timestamp
                if isinstance(start_time, firestore_module.Timestamp):
                    # Firestore Timestamp object - convert to datetime
                    date_obj = start_time.to_datetime() if hasattr(start_time, 'to_datetime') else datetime.fromtimestamp(start_time.timestamp())
                    date_str = date_obj.strftime("%Y-%m-%d")
                elif isinstance(start_time, datetime):
                    # Python datetime
                    date_str = start_time.strftime("%Y-%m-%d")
                elif hasattr(start_time, 'date'):
                    # Datetime-like object with date() method
                    date_str = start_time.date().strftime("%Y-%m-%d")
                elif isinstance(start_time, str):
                    # String format - try to parse
                    try:
                        date_obj = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except:
                        date_str = datetime.now().strftime("%Y-%m-%d")
                else:
                    # Fallback to current date
                    date_str = datetime.now().strftime("%Y-%m-%d")
                # Get attendance for that class and date
                attendance_records = self.get_attendance_for_class(class_id, date_str)
                
                # Filter to only students in this session
                recognized_students = session.get('recognizedStudents', [])
                if recognized_students:
                    # Return attendance for recognized students only
                    filtered_records = [
                        record for record in attendance_records
                        if record.get('studentId') in recognized_students
                    ]
                    return filtered_records
                
                return attendance_records
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting attendance for session: {e}")
            return []
    
    def save_student_data(self, student_id: str, student_name: str, 
                         class_id: str, additional_data: Dict = None) -> bool:
        """
        Save student data to Firebase.
        
        Args:
            student_id: Unique student identifier
            student_name: Name of the student
            class_id: Class the student belongs to
            additional_data: Additional student data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            student_data = {
                'studentId': student_id,
                'studentName': student_name,
                'classId': class_id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            if additional_data:
                student_data.update(additional_data)
            
            self.db.collection('students').document(student_id).set(student_data, merge=True)
            print(f"✅ Student data saved: {student_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving student data: {e}")
            return False
    
    def get_students_for_class(self, class_id: str) -> List[Dict]:
        """
        Get all students for a specific class.
        
        Args:
            class_id: ID of the class
            
        Returns:
            List of student records
        """
        try:
            query = self.db.collection('students').where('classId', '==', class_id)
            docs = query.stream()
            
            students = []
            for doc in docs:
                student = doc.to_dict()
                student['id'] = doc.id
                students.append(student)
            
            return students
            
        except Exception as e:
            print(f"❌ Error getting students: {e}")
            return []
    
    def update_attendance_batch(self, class_id: str, attendance_records: Dict[str, Any]) -> bool:
        """
        Update attendance records in batch.
        
        Args:
            class_id: ID of the class
            attendance_records: Dictionary of student_id -> attendance data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            batch = self.db.batch()
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            for student_id, data in attendance_records.items():
                record_id = f"{class_id}_{student_id}_{today_str}"
                doc_ref = self.db.collection('attendance').document(record_id)
                
                attendance_data = {
                    'classId': class_id,
                    'studentId': student_id,
                    'date': today_str,
                    'status': data.get('status', 'present'),
                    'presenceTime': data.get('presence_time', 0),
                    'attendancePercentage': data.get('attendance_percentage', 0),
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'updatedAt': datetime.now().isoformat()
                }
                
                batch.set(doc_ref, attendance_data, merge=True)
            
            batch.commit()
            print(f"✅ Batch attendance update completed for class {class_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating attendance batch: {e}")
            return False

# Global Firebase manager instance
firebase_manager = None

def get_firebase_manager() -> FirebaseManager:
    """Get the global Firebase manager instance."""
    global firebase_manager
    if firebase_manager is None:
        firebase_manager = FirebaseManager()
    return firebase_manager

def initialize_firebase(service_account_path: str = "serviceAccountKey.json") -> FirebaseManager:
    """Initialize Firebase and return the manager instance."""
    global firebase_manager
    firebase_manager = FirebaseManager(service_account_path)
    return firebase_manager
