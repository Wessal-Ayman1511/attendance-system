import os
import shutil
import base64
from flask import jsonify, request

# Base directory for student images
STUDENTS_DIR = "Smart Attendance System/Images"


def add_student_from_api(student_name, image_data_list):
    """
    Create a student folder and save received base64 images.
    Used when images are captured from frontend (browser camera).
    """

    student_name = student_name.strip().replace(" ", "_")
    student_folder = os.path.join(STUDENTS_DIR, student_name)

    # Create base directory if missing
    if not os.path.exists(STUDENTS_DIR):
        os.makedirs(STUDENTS_DIR)

    # Prevent overwriting existing student folder
    if os.path.exists(student_folder):
        return jsonify({
            "status": "error",
            "message": f"Student '{student_name}' already exists! Delete it first to recapture."
        }), 400

    os.makedirs(student_folder)

    saved_count = 0
    for idx, img_data in enumerate(image_data_list):
        try:
            # Remove 'data:image/jpeg;base64,' prefix if present
            if "," in img_data:
                img_data = img_data.split(",")[1]

            img_bytes = base64.b64decode(img_data)
            filename = os.path.join(student_folder, f"{student_name}_{idx+1}.jpg")

            with open(filename, "wb") as f:
                f.write(img_bytes)
            saved_count += 1
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to save image {idx+1}: {str(e)}"
            }), 500

    return jsonify({
        "status": "success",
        "student": student_name,
        "photos_saved": saved_count,
        "folder": student_folder
    })


def remove_student(student_name):
    """
    Delete a student's image folder.
    """
    student_name = student_name.strip().replace(" ", "_")
    student_folder = os.path.join(STUDENTS_DIR, student_name)

    if os.path.exists(student_folder):
        shutil.rmtree(student_folder)
        return jsonify({
            "status": "success",
            "message": f"Student '{student_name}' removed successfully!"
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Student '{student_name}' not found."
        }), 404
