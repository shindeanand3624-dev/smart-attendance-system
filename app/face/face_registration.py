import cv2
import os
import mysql.connector


# ==========================================
# CONFIGURATION
# ==========================================

IMAGE_FOLDER = "student_images"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "smart_attendance"
}


# ==========================================
# CREATE IMAGE FOLDER
# ==========================================

os.makedirs(IMAGE_FOLDER, exist_ok=True)


# ==========================================
# STUDENT DETAILS
# ==========================================

student_id = input("Enter Student ID: ").strip()
student_name = input("Enter Student Name: ").strip()
roll_number = input("Enter Roll Number: ").strip()
email = input("Enter Email: ").strip()
phone = input("Enter Phone: ").strip()
department = input("Enter Department: ").strip()
year = input("Enter Year: ").strip()


# ==========================================
# CHECK REQUIRED DETAILS
# ==========================================

if student_id == "" or student_name == "" or roll_number == "":
    print("Student ID, Name and Roll Number are required.")
    exit()


# ==========================================
# IMAGE FILE PATH
# ==========================================

safe_name = student_name.replace(" ", "_")

file_name = student_id + "_" + safe_name + ".jpg"

file_path = os.path.join(
    IMAGE_FOLDER,
    file_name
)


# ==========================================
# FACE DETECTOR
# ==========================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


# ==========================================
# START CAMERA
# ==========================================

print("----------------------------------------")
print("Starting Camera...")
print("Look directly at the camera.")
print("SPACE = Capture Face")
print("Q = Cancel")
print("----------------------------------------")

camera = cv2.VideoCapture(0)


if not camera.isOpened():
    print("Error: Cannot access webcam.")
    exit()


face_captured = False


# ==========================================
# CAMERA LOOP
# ==========================================

while True:

    success, frame = camera.read()

    if not success:
        print("Cannot read webcam.")
        break

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    for (x, y, w, h) in faces:

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Face Detected",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        "SPACE = Capture | Q = Cancel",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.imshow(
        "Student Face Registration",
        frame
    )

    key = cv2.waitKey(1) & 0xFF


    # ======================================
    # CAPTURE FACE
    # ======================================

    if key == ord(" "):

        if len(faces) == 0:
            print("No face detected.")
            continue

        if len(faces) > 1:
            print("Multiple faces detected.")
            print("Only one student should be visible.")
            continue

        cv2.imwrite(
            file_path,
            frame
        )

        face_captured = True

        print("----------------------------------------")
        print("Face captured successfully!")
        print("Image:", file_path)
        print("----------------------------------------")

        break


    # ======================================
    # CANCEL
    # ======================================

    if key == ord("q"):

        print("Registration cancelled.")
        break


# ==========================================
# CLOSE CAMERA
# ==========================================

camera.release()

cv2.destroyAllWindows()


# ==========================================
# SAVE STUDENT TO MYSQL
# ==========================================

if face_captured:

    try:

        connection = mysql.connector.connect(
            **DB_CONFIG
        )

        cursor = connection.cursor()

        query = """
        INSERT INTO students
        (
            student_id,
            name,
            roll_number,
            email,
            phone,
            department,
            year,
            face_image
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """

        values = (
            student_id,
            student_name,
            roll_number,
            email,
            phone,
            department,
            year,
            file_path
        )

        cursor.execute(
            query,
            values
        )

        connection.commit()

        print("----------------------------------------")
        print("STUDENT REGISTERED SUCCESSFULLY")
        print("----------------------------------------")
        print("Student ID :", student_id)
        print("Name       :", student_name)
        print("Roll Number:", roll_number)
        print("Face Image :", file_path)
        print("----------------------------------------")

        cursor.close()
        connection.close()

    except mysql.connector.Error as error:

        print("----------------------------------------")
        print("DATABASE ERROR")
        print("----------------------------------------")
        print(error)

else:

    print("Student was not registered.")