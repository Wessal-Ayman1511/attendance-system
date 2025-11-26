# =========================================================
# session_state.py
# =========================================================
# Minimal in-memory session management for API-based frame uploads.
# Scheduling removed; sessions are controlled by API start/stop calls.
# =========================================================

from datetime import datetime
from main import mark_attendance
from flask import jsonify
import time
from firebase_config import get_firebase_manager
import threading

# ---------------------------------------------------------
# Concurrent per-class session state (thread-safe)
# ---------------------------------------------------------
_sessions_lock = threading.RLock()
_sessions_by_class = {}
"""
_sessions_by_class structure:
{
  class_id: {
    "is_active": bool,
    "session_name": str,
    "attendance_records": { name: frames_count },
    "start_time": datetime,
  }
}
"""


def start_session(class_id: str, session_name: str = None):
    """Start a new manual session for a specific class (concurrent-safe)."""
    if not class_id:
        return jsonify({"status": "error", "message": "class_id is required"}), 400
    with _sessions_lock:
        sess = _sessions_by_class.get(class_id)
        if sess and sess.get("is_active"):
            return jsonify({"status": "already_active", "class_id": class_id}), 409
        _sessions_by_class[class_id] = {
            "is_active": True,
            "session_name": session_name or f"{class_id}_session",
            "attendance_records": {},
            "start_time": datetime.now(),
        }
        s = _sessions_by_class[class_id]
        return jsonify({
            "status": "started",
            "class_id": class_id,
            "session_name": s["session_name"],
            "start_time": s["start_time"].isoformat()
        })


def stop_session(class_id: str):
    """Stop the session for a specific class and return summary."""
    if not class_id:
        return jsonify({"status": "error", "message": "class_id is required"}), 400
    with _sessions_lock:
        sess = _sessions_by_class.get(class_id)
        if not sess or not sess.get("is_active"):
            return jsonify({"status": "inactive", "message": "No active session."}), 400
        end_time = datetime.now()
        start_time = sess.get("start_time")
        duration_seconds = int((end_time - start_time).total_seconds()) if start_time else 0
        attendance_records = dict(sess.get("attendance_records", {}))
        summary = {
            "session_active": False,
            "session_name": sess.get("session_name"),
            "class_id": class_id,
            "attendance_records": attendance_records,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
        }
        # clear
        _sessions_by_class[class_id] = {
            "is_active": False,
            "session_name": None,
            "attendance_records": {},
            "start_time": None,
        }
        return jsonify(summary)


def get_session_status(class_id: str):
    """Return whether a class session is currently active."""
    if not class_id:
        return jsonify({"status": "error", "message": "class_id is required"}), 400
    with _sessions_lock:
        sess = _sessions_by_class.get(class_id) or {}
        st = sess.get("start_time")
        return jsonify({
            "session_active": bool(sess.get("is_active")),
            "session_name": sess.get("session_name"),
            "class_id": class_id,
            "start_time": st.isoformat() if st else None
        })


def list_scheduled_sessions():
    """Scheduling removed; return empty list for backward compatibility."""
    return jsonify({"scheduled_jobs": []})


def cancel_session(session_id):
    """Scheduling removed; nothing to cancel."""
    return jsonify({"status": "not_supported"}), 400


    # (get_session_status defined above)


# ---------------------------------------------------------
# API helper: record recognition result (called by Flask route)
# ---------------------------------------------------------
def record_recognition_results(recognized_names):
    """
    Called by /api/recognize_image endpoint.
    Updates attendance during active session.
    """
    return jsonify({"status": "error", "message": "class_id required"}), 400


def record_recognition_results_for_class(recognized_names, class_id: str):
    """Update attendance for a specific class session."""
    if not class_id:
        return jsonify({"status": "error", "message": "class_id is required"}), 400
    with _sessions_lock:
        sess = _sessions_by_class.get(class_id)
        if not sess or not sess.get("is_active"):
            return jsonify({"status": "inactive", "message": "No active session."}), 403
        records = sess.setdefault("attendance_records", {})
        for name in recognized_names:
            if name != "Unknown":
                records[name] = records.get(name, 0) + 1
        return jsonify({"status": "recorded", "updated": records})

def get_current_session_data(class_id: str):
    """Get session data for a specific class."""
    if not class_id:
        return None
    with _sessions_lock:
        sess = _sessions_by_class.get(class_id)
        if not sess:
            return None
        return {
            "session_active": bool(sess.get("is_active")),
            "session_name": sess.get("session_name"),
            "class_id": class_id,
            "attendance_records": dict(sess.get("attendance_records", {})),
            "start_time": sess.get("start_time"),
        }

def clear_session_data(class_id: str = None):
    """Clear session data for a class or all."""
    with _sessions_lock:
        if class_id:
            _sessions_by_class[class_id] = {
                "is_active": False,
                "session_name": None,
                "attendance_records": {},
                "start_time": None,
            }
        else:
            _sessions_by_class.clear()
