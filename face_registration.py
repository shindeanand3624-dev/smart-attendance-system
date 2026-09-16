import cv2
import os
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
# FACE IMAGE FOLDER
# =========================================================

FACE_FOLDER = os.path.join(
    "app",
    "static",
    "uploads",
    "faces"
)

os.makedirs(
    FACE_FOLDER,
    exist_ok=True
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
# REGISTER FACE
# =========================================================

def register_face(student_id):

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("ERROR: Camera could not be opened.")

        return False


    print()
    print("----------------------------------------")
    print("FACE REGISTRATION")
    print("----------------------------------------")
    print("Look directly at the camera.")
    print("Press SPACE to capture your face.")
    print("Press Q to cancel.")
    print("----------------------------------------")


    captured = False


    while True:

        ret, frame = camera.read()


        if not ret:

            print("ERROR: Could not read camera.")

            break


        # -------------------------------------------------
        # Detect face
        # -------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        import face_recognition


        face_locations = face_recognition.face_locations(
            rgb_frame
        )


        # -------------------------------------------------
        # Draw face rectangle
        # -------------------------------------------------

        for top, right, bottom, left in face_locations:

            cv2.rectangle(
                frame,
                (left, top),
                (right, bottom),
                (0, 255, 0),
                2
            )


        # -------------------------------------------------
        # Display information
        # -------------------------------------------------

        cv2.putText(
            frame,
            f"Faces detected: {len(face_locations)}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            "SPACE = Capture | Q = Cancel",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        cv2.imshow(
            "SVM - Face Registration",
            frame
        )


        key = cv2.waitKey(1) & 0xFF


        # -------------------------------------------------
        # Capture
        # -------------------------------------------------

        if key == 32:

            if len(face_locations) == 1:

                file_name = f"{student_id}.jpg"

                file_path = os.path.join(
                    FACE_FOLDER,
                    file_name
                )


                success = cv2.imwrite(
                    file_path,
                    frame
                )


                if success:

                    print()
                    print("Face captured successfully!")
                    print(
                        "Saved:",
                        file_path
                    )


                    # -------------------------------------
                    # SAVE PATH TO DATABASE
                    # -------------------------------------

                    connection = None
                    cursor = None


                    try:

                        connection = get_db_connection()

                        cursor = connection.cursor()


                        query = """
                        UPDATE students
                        SET face_image = %s
                        WHERE student_id = %s
                        """


                        cursor.execute(
                            query,
                            (
                                file_path,
                                student_id
                            )
                        )


                        connection.commit()


                        if cursor.rowcount == 0:

                            print(
                                "WARNING: Student ID not found."
                            )

                            captured = False

                        else:

                            print(
                                "Face path saved to database."
                            )

                            captured = True


                    except mysql.connector.Error as e:

                        print(
                            "MySQL Error:",
                            e
                        )


                    finally:

                        if cursor:

                            cursor.close()

                        if connection:

                            connection.close()


                break


            elif len(face_locations) == 0:

                print(
                    "No face detected. Try again."
                )


            else:

                print(
                    "Multiple faces detected."
                )

                print(
                    "Only one person should be in front of camera."
                )


        # -------------------------------------------------
        # Cancel
        # -------------------------------------------------

        elif key == ord("q"):

            print(
                "Face registration cancelled."
            )

            break


    camera.release()

    cv2.destroyAllWindows()


    return captured


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("SVM SMART ATTENDANCE")
    print("FACE REGISTRATION")
    print("========================================")


    student_id = input(
        "Enter Student ID: "
    ).strip()


    if not student_id:

        print(
            "Student ID is required."
        )

    else:

        result = register_face(
            student_id
        )


        print()


        if result:

            print(
                "FACE REGISTRATION SUCCESSFUL!"
            )

        else:

            print(
                "FACE REGISTRATION FAILED."
            )