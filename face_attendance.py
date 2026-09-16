import cv2
import os
import face_recognition
import mysql.connector


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "smart_attendance"
}


# =========================================================
# FACE IMAGE BASE FOLDER
# =========================================================

FACE_BASE_FOLDER = os.path.join(
    "app",
    "static",
    "uploads",
    "faces"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


# =========================================================
# LOAD REGISTERED STUDENT FACES
# =========================================================

def load_registered_faces():

    connection = None
    cursor = None

    known_face_encodings = []
    known_student_ids = []

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
        SELECT
            student_id,
            name,
            face_image
        FROM students
        WHERE face_image IS NOT NULL
        AND face_image != ''
        AND status = 'ACTIVE'
        """

        cursor.execute(query)

        students = cursor.fetchall()

        print()
        print("----------------------------------------")
        print("LOADING REGISTERED FACES")
        print("----------------------------------------")

        for student in students:

            student_id = str(
                student["student_id"]
            )

            image_path = student["face_image"]

            # Convert Windows DB path if necessary
            image_path = image_path.replace(
                "\\",
                os.sep
            )

            # If path doesn't exist, try using only filename
            if not os.path.exists(image_path):

                filename = os.path.basename(
                    image_path
                )

                image_path = os.path.join(
                    FACE_BASE_FOLDER,
                    filename
                )

            print(
                f"Student: {student_id} | "
                f"Name: {student['name']}"
            )

            print(
                f"Image: {image_path}"
            )

            if not os.path.exists(image_path):

                print(
                    "WARNING: Image not found."
                )

                continue

            # -----------------------------------------
            # LOAD IMAGE
            # -----------------------------------------

            image = face_recognition.load_image_file(
                image_path
            )

            # -----------------------------------------
            # CREATE FACE ENCODING
            # -----------------------------------------

            encodings = face_recognition.face_encodings(
                image
            )

            if len(encodings) == 0:

                print(
                    "WARNING: No face found in image."
                )

                continue

            if len(encodings) > 1:

                print(
                    "WARNING: Multiple faces found."
                )

                continue

            known_face_encodings.append(
                encodings[0]
            )

            known_student_ids.append(
                student_id
            )

            print(
                "Face encoding loaded successfully."
            )

            print()

        print("----------------------------------------")

        print(
            f"Total registered faces: "
            f"{len(known_face_encodings)}"
        )

        print("----------------------------------------")

        return (
            known_face_encodings,
            known_student_ids
        )

    except mysql.connector.Error as e:

        print(
            "MySQL Error:",
            e
        )

        return [], []

    except Exception as e:

        print(
            "Error loading faces:",
            e
        )

        return [], []

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# RECOGNIZE STUDENT
# =========================================================

def recognize_student(student_id=None):

    print()
    print("========================================")
    print("SVM FACE RECOGNITION")
    print("========================================")

    # =====================================================
    # LOAD REGISTERED FACES
    # =====================================================

    (
        known_face_encodings,
        known_student_ids
    ) = load_registered_faces()

    if not known_face_encodings:

        return {
            "success": False,
            "message": "No registered faces found."
        }

    # =====================================================
    # OPEN CAMERA
    # =====================================================

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        return {
            "success": False,
            "message": "Camera could not be opened."
        }

    print()
    print("----------------------------------------")
    print("CAMERA STARTED")
    print("----------------------------------------")
    print("Look directly at the camera.")
    print("Press Q to cancel.")
    print("----------------------------------------")

    recognized_student = None

    while True:

        ret, frame = camera.read()

        if not ret:

            print(
                "ERROR: Could not read camera."
            )

            break

        # =================================================
        # RESIZE FRAME
        # =================================================

        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=0.25,
            fy=0.25
        )

        # =================================================
        # CONVERT BGR TO RGB
        # =================================================

        rgb_small_frame = cv2.cvtColor(
            small_frame,
            cv2.COLOR_BGR2RGB
        )

        # =================================================
        # DETECT FACES
        # =================================================

        face_locations = face_recognition.face_locations(
            rgb_small_frame
        )

        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations
        )

        # =================================================
        # CHECK EACH FACE
        # =================================================

        for face_encoding, face_location in zip(
            face_encodings,
            face_locations
        ):

            # ---------------------------------------------
            # COMPARE WITH REGISTERED FACES
            # ---------------------------------------------

            matches = face_recognition.compare_faces(
                known_face_encodings,
                face_encoding,
                tolerance=0.50
            )

            face_distances = face_recognition.face_distance(
                known_face_encodings,
                face_encoding
            )

            if len(face_distances) > 0:

                best_match_index = face_distances.argmin()

            else:

                best_match_index = None

            # ---------------------------------------------
            # FACE MATCHED
            # ---------------------------------------------

            if (
                best_match_index is not None
                and matches[best_match_index]
            ):

                matched_student_id = (
                    known_student_ids[
                        best_match_index
                    ]
                )

                # -----------------------------------------
                # IF SPECIFIC STUDENT WAS REQUESTED
                # -----------------------------------------

                if (
                    student_id is not None
                    and str(matched_student_id)
                    != str(student_id)
                ):

                    print(
                        "Face belongs to another student."
                    )

                    label = "Wrong Student"

                else:

                    recognized_student = (
                        matched_student_id
                    )

                    label = (
                        f"Matched: "
                        f"{matched_student_id}"
                    )

                    print()
                    print(
                        "FACE RECOGNIZED!"
                    )

                    print(
                        "Student ID:",
                        matched_student_id
                    )

                    break

            else:

                label = "Unknown Face"

            # =================================================
            # DRAW FACE BOX
            # =================================================

            top, right, bottom, left = face_location

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(
                frame,
                (left, top),
                (right, bottom),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                label,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # =================================================
        # SHOW CAMERA
        # =================================================

        cv2.putText(
            frame,
            "Q = Exit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "SVM - Face Recognition",
            frame
        )

        # =================================================
        # SUCCESS
        # =================================================

        if recognized_student is not None:

            cv2.waitKey(1000)

            break

        # =================================================
        # QUIT
        # =================================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print(
                "Face recognition cancelled."
            )

            break

    # =====================================================
    # RELEASE CAMERA
    # =====================================================

    camera.release()

    cv2.destroyAllWindows()

    # =====================================================
    # RESULT
    # =====================================================

    if recognized_student is not None:

        return {
            "success": True,
            "student_id": recognized_student,
            "message": "Face recognized successfully."
        }

    return {
        "success": False,
        "message": "Face not recognized."
    }


# =========================================================
# TEST FACE RECOGNITION
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("SVM SMART ATTENDANCE")
    print("FACE RECOGNITION TEST")
    print("========================================")

    result = recognize_student()

    print()

    if result["success"]:

        print(
            "FACE RECOGNITION SUCCESSFUL!"
        )

        print(
            "Student ID:",
            result["student_id"]
        )

    else:

        print(
            "FACE RECOGNITION FAILED."
        )

        print(
            result["message"]
        )