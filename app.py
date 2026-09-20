#cd C:\Users\DELL SmartAttendance.\start_attendance.bat
#cd C:\Users\DELL SmartAttendance

#.\start_attendance.bat
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

import mysql.connector
import os
import cv2
import base64
import io
import uuid
from datetime import datetime, timedelta, time
try:
    import qrcode
except ImportError:
    qrcode = None

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from face_attendance import recognize_student


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.secret_key = "svm-smart-attendance-secret-key"


# =========================================================
# MYSQL DATABASE CONFIGURATION
# =========================================================
import os

# Create Aiven CA certificate on the server from an environment variable
ssl_ca_path = "ca.pem"

if os.environ.get("DB_SSL_CA"):
    with open(ssl_ca_path, "w") as f:
        f.write(os.environ["DB_SSL_CA"])
        
DB_CONFIG = {
    "host": "mysql-3bace686-shindeanand3624-afc6.e.aivencloud.com",
    "port": 26165,
    "user": "avnadmin",
    "password": os.environ.get("DB_PASSWORD"),
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}


# =========================================================
# FACE IMAGE FOLDER
# =========================================================

FACE_BASE_FOLDER = os.path.join(
    app.static_folder,
    "uploads",
    "faces"
)

os.makedirs(
    FACE_BASE_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        ssl_ca=DB_CONFIG["ssl_ca"]
    )

# =========================================================
# ATTENDANCE TIME RESTRICTION
# =========================================================

ATTENDANCE_START_TIME = time(10, 0)   # 10:00 AM
ATTENDANCE_END_TIME = time(15, 0)     # 3:00 PM


def is_attendance_time_allowed():

    current_time = datetime.now().time()

    return (
        ATTENDANCE_START_TIME
        <= current_time
        <= ATTENDANCE_END_TIME
    )

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    print("LOGIN ROUTE CALLED")
    print("METHOD:", request.method)
    if request.method == "GET":
        return render_template("index.html")

    login_type = request.form.get(
        "login_type",
        "student"
    ).strip().lower()

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if not username:

        flash(
            "Please enter your Student ID or Teacher ID.",
            "error"
        )

        return redirect(url_for("home"))

    if not password:

        flash(
            "Please enter your password.",
            "error"
        )

        return redirect(url_for("home"))


    # =====================================================
    # STUDENT LOGIN
    # =====================================================

    if login_type == "student":

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            query = """
                SELECT
                    id,
                    student_id,
                    name,
                    roll_number,
                    email,
                    phone,
                    department,
                    year,
                    password,
                    status
                FROM students
                WHERE student_id = %s
                   OR email = %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (
                    username,
                    username
                )
            )

            student = cursor.fetchone()

            if student is None:

                flash(
                    "Invalid Student ID/Email or Password.",
                    "error"
                )

                return redirect(url_for("home"))

            student_status = str(
                student.get(
                    "status",
                    "ACTIVE"
                )
            ).upper()

            if student_status != "ACTIVE":

                flash(
                    "Your student account is not active.",
                    "error"
                )

                return redirect(url_for("home"))

            if not check_password_hash(
                student["password"],
                password
            ):

                flash(
                    "Invalid Student ID/Email or Password.",
                    "error"
                )

                return redirect(url_for("home"))

            session.clear()

            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
            session["student_roll_number"] = student["roll_number"]
            session["student_department"] = student["department"]
            session["student_year"] = student["year"]
            session["user_type"] = "student"

            flash(
                f"Welcome, {student['name']}!",
                "success"
            )

            return redirect(
                url_for("student_dashboard")
            )

        except mysql.connector.Error as e:

            print(
                "Student Login MySQL Error:",
                e
            )

            flash(
                "Database error occurred.",
                "error"
            )

            return redirect(url_for("home"))

        except Exception as e:

            print(
                "Student Login Error:",
                e
            )

            flash(
                "Something went wrong.",
                "error"
            )

            return redirect(url_for("home"))

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()


    # =====================================================
    # TEACHER LOGIN
    # =====================================================

    elif login_type == "teacher":

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            query = """
                SELECT
                    id,
                    teacher_id,
                    name,
                    email,
                    password
                FROM teachers
                WHERE teacher_id = %s
                   OR email = %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (
                    username,
                    username
                )
            )

            teacher = cursor.fetchone()

            if teacher is None:

                flash(
                    "Invalid Teacher ID/Email or Password.",
                    "error"
                )

                return redirect(url_for("home"))

            if not check_password_hash(
                teacher["password"],
                password
            ):

                flash(
                    "Invalid Teacher ID/Email or Password.",
                    "error"
                )

                return redirect(url_for("home"))

            session.clear()

            session["teacher_id"] = teacher["teacher_id"]
            session["teacher_name"] = teacher["name"]
            session["teacher_email"] = teacher["email"]
            session["user_type"] = "teacher"

            flash(
                f"Welcome, {teacher['name']}!",
                "success"
            )

            return redirect(
                url_for("teacher_dashboard")
            )

        except mysql.connector.Error as e:

            print(
                "Teacher Login MySQL Error:",
                e
            )

            flash(
                "Database error occurred.",
                "error"
            )

            return redirect(url_for("home"))

        except Exception as e:

            print(
                "Teacher Login Error:",
                e
            )

            flash(
                "Something went wrong.",
                "error"
            )

            return redirect(url_for("home"))

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    else:

        flash(
            "Invalid login type.",
            "error"
        )

        return redirect(url_for("home"))


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "GET":

        return render_template(
            "forgot_password.html"
        )

    user_type = request.form.get(
        "user_type",
        "student"
    ).strip().lower()

    email = request.form.get(
        "email",
        ""
    ).strip()

    new_password = request.form.get(
        "new_password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()

    if not email:

        flash(
            "Please enter your registered email.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    if not new_password:

        flash(
            "Please enter a new password.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    if len(new_password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    if new_password != confirm_password:

        flash(
            "New password and confirm password do not match.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # STUDENT
        # =================================================

        if user_type == "student":

            query = """
                SELECT
                    id,
                    student_id,
                    email
                FROM students
                WHERE email = %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (email,)
            )

            student = cursor.fetchone()

            if student is None:

                flash(
                    "No student account found with this email.",
                    "error"
                )

                return redirect(
                    url_for("forgot_password")
                )

            hashed_password = generate_password_hash(
                new_password
            )

            update_query = """
                UPDATE students
                SET password = %s
                WHERE id = %s
            """

            cursor.execute(
                update_query,
                (
                    hashed_password,
                    student["id"]
                )
            )

            connection.commit()

            flash(
                "Student password changed successfully! Please login.",
                "success"
            )

            return redirect(
                url_for("home")
            )


        # =================================================
        # TEACHER
        # =================================================

        elif user_type == "teacher":

            query = """
                SELECT
                    id,
                    teacher_id,
                    email
                FROM teachers
                WHERE email = %s
                LIMIT 1
            """

            cursor.execute(
                query,
                (email,)
            )

            teacher = cursor.fetchone()

            if teacher is None:

                flash(
                    "No teacher account found with this email.",
                    "error"
                )

                return redirect(
                    url_for("forgot_password")
                )

            hashed_password = generate_password_hash(
                new_password
            )

            update_query = """
                UPDATE teachers
                SET password = %s
                WHERE id = %s
            """

            cursor.execute(
                update_query,
                (
                    hashed_password,
                    teacher["id"]
                )
            )

            connection.commit()

            flash(
                "Teacher password changed successfully! Please login.",
                "success"
            )

            return redirect(
                url_for("home")
            )

        else:

            flash(
                "Invalid account type.",
                "error"
            )

            return redirect(
                url_for("forgot_password")
            )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Forgot Password MySQL Error:",
            e
        )

        flash(
            "Database error occurred.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Forgot Password Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    roll_number = request.form.get(
        "roll_number",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    year = request.form.get(
        "year",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()


    if not student_id:

        flash(
            "Student ID is required.",
            "error"
        )

        return redirect(url_for("register"))

    if not student_name:

        flash(
            "Student Name is required.",
            "error"
        )

        return redirect(url_for("register"))

    if not roll_number:

        flash(
            "Roll Number is required.",
            "error"
        )

        return redirect(url_for("register"))

    if not department:

        flash(
            "Please select Department.",
            "error"
        )

        return redirect(url_for("register"))

    if not year:

        flash(
            "Please select Academic Year.",
            "error"
        )

        return redirect(url_for("register"))

    if not password:

        flash(
            "Password is required.",
            "error"
        )

        return redirect(url_for("register"))

    if len(password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "error"
        )

        return redirect(url_for("register"))

    if password != confirm_password:

        flash(
            "Password and Confirm Password do not match.",
            "error"
        )

        return redirect(url_for("register"))

    hashed_password = generate_password_hash(
        password
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO students
            (
                student_id,
                name,
                roll_number,
                email,
                password,
                phone,
                department,
                year,
                face_image,
                fingerprint_id,
                status
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
            email if email else None,
            hashed_password,
            phone if phone else None,
            department,
            year,
            None,
            None,
            "ACTIVE"
        )

        cursor.execute(
            query,
            values
        )

        connection.commit()

        flash(
            "Student registered successfully! You can now login.",
            "success"
        )

        return redirect(
            url_for("home")
        )

    except mysql.connector.IntegrityError as e:

        if connection:
            connection.rollback()

        print(
            "Student Duplicate Error:",
            e
        )

        flash(
            "Student ID, Roll Number, or Email already exists.",
            "error"
        )

        return redirect(
            url_for("register")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Student MySQL Error:",
            e
        )

        flash(
            "Database error occurred.",
            "error"
        )

        return redirect(
            url_for("register")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Student Registration Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("register")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ATTENDANCE STATISTICS
# =========================================================

def get_attendance_statistics(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT

                COUNT(*) AS total_classes,

                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(status)) = 'PRESENT'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS present_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(status)) = 'ABSENT'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS absent_count

            FROM attendance

            WHERE student_id = %s
        """

        cursor.execute(
            query,
            (student_id,)
        )

        result = cursor.fetchone()

        if not result:

            return {
                "total_classes": 0,
                "present_count": 0,
                "absent_count": 0,
                "attendance_percentage": 0.0
            }

        total_classes = int(
            result["total_classes"] or 0
        )

        present_count = int(
            result["present_count"] or 0
        )

        absent_count = int(
            result["absent_count"] or 0
        )

        if total_classes > 0:

            attendance_percentage = (
                present_count / total_classes
            ) * 100

        else:

            attendance_percentage = 0.0

        return {
            "total_classes": total_classes,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": round(
                attendance_percentage,
                2
            )
        }

    except Exception as e:

        print(
            "Attendance Statistics Error:",
            e
        )

        return {
            "total_classes": 0,
            "present_count": 0,
            "absent_count": 0,
            "attendance_percentage": 0.0
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# FACE REGISTRATION PAGE
# =========================================================

@app.route("/student/face-register")
def face_register():

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                student_id,
                name,
                face_image,
                status
            FROM students
            WHERE student_id = %s
            LIMIT 1
        """

        cursor.execute(
            query,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:

            flash(
                "Student account not found.",
                "error"
            )

            return redirect(
                url_for("student_dashboard")
            )

        if str(
            student.get(
                "status",
                "ACTIVE"
            )
        ).upper() != "ACTIVE":

            flash(
                "Your student account is not active.",
                "error"
            )

            return redirect(
                url_for("student_dashboard")
            )

        if student.get("face_image"):

            flash(
                "Your face is already registered.",
                "success"
            )

            return redirect(
                url_for("student_dashboard")
            )

        return render_template(
            "face_register.html",
            student_id=student["student_id"],
            student_name=student["name"]
        )

    except mysql.connector.Error as e:

        print(
            "Face Registration MySQL Error:",
            e
        )

        flash(
            "Database error occurred.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except Exception as e:

        print(
            "Face Registration Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# =========================================================
# SAVE REGISTERED FACE
# =========================================================

@app.route("/student/save-face", methods=["POST"])
def save_face():

    # -----------------------------------------------------
    # CHECK STUDENT LOGIN
    # -----------------------------------------------------

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    # -----------------------------------------------------
    # GET FACE IMAGE
    # -----------------------------------------------------

    face_image = request.form.get(
        "face_image",
        ""
    ).strip()

    if not face_image:

        flash(
            "Please capture your face first.",
            "error"
        )

        return redirect(
            url_for("face_register")
        )

    # -----------------------------------------------------
    # CHECK BASE64 FORMAT
    # -----------------------------------------------------

    if "," not in face_image:

        flash(
            "Invalid face image.",
            "error"
        )

        return redirect(
            url_for("face_register")
        )

    try:

        # =================================================
        # IMPORT REQUIRED MODULES
        # =================================================

        import base64
        import os

        # =================================================
        # REMOVE BASE64 HEADER
        # =================================================

        image_data = face_image.split(
            ",",
            1
        )[1]

        # =================================================
        # DECODE IMAGE
        # =================================================

        image_bytes = base64.b64decode(
            image_data
        )

        # =================================================
        # FACE STORAGE FOLDER
        # =================================================

        face_folder = os.path.join(
            app.static_folder,
            "uploads",
            "faces"
        )

        # Create folder if it does not exist

        os.makedirs(
            face_folder,
            exist_ok=True
        )

        # =================================================
        # IMAGE FILE NAME
        # =================================================

        filename = (
            f"{student_id}_face.jpg"
        )

        image_path = os.path.join(
            face_folder,
            filename
        )

        # =================================================
        # SAVE IMAGE
        # =================================================

        with open(
            image_path,
            "wb"
        ) as file:

            file.write(
                image_bytes
            )

        # =================================================
        # DATABASE
        # =================================================

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor()

            # Store relative path in database

            db_image_path = os.path.join(
                "app",
                "static",
                "uploads",
                "faces",
                filename
            )

            update_query = """
                UPDATE students
                SET face_image = %s
                WHERE student_id = %s
            """

            cursor.execute(
                update_query,
                (
                    db_image_path,
                    student_id
                )
            )

            connection.commit()

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

        # =================================================
        # SUCCESS
        # =================================================

        print()
        print("----------------------------------------")
        print("FACE REGISTERED SUCCESSFULLY")
        print("----------------------------------------")
        print(
            "Student ID:",
            student_id
        )
        print(
            "Image:",
            image_path
        )
        print("----------------------------------------")

        flash(
            "Face registered successfully!",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except Exception as e:

        print(
            "Save Face Error:",
            e
        )

        flash(
            "Unable to save face image.",
            "error"
        )

        return redirect(
            url_for("face_register")
        )

 


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student/dashboard")
def student_dashboard():

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        stats = get_attendance_statistics(
            student_id
        )

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # RECENT ATTENDANCE
        # -------------------------------------------------

        recent_query = """
            SELECT
                attendance_date,
                attendance_time,
                method,
                status
            FROM attendance
            WHERE student_id = %s
            ORDER BY
                attendance_date DESC,
                attendance_time DESC
            LIMIT 10
        """

        cursor.execute(
            recent_query,
            (student_id,)
        )

        recent_attendance = cursor.fetchall()

        # -------------------------------------------------
        # RECENT LEAVE REQUESTS
        # -------------------------------------------------

        leave_requests = []

        try:

            leave_query = """
                SELECT
                    id,
                    from_date,
                    to_date,
                    reason,
                    status
                FROM leave_requests
                WHERE student_id = %s
                ORDER BY id DESC
                LIMIT 10
            """

            cursor.execute(
                leave_query,
                (student_id,)
            )

            leave_requests = cursor.fetchall()

        except mysql.connector.Error:

            leave_requests = []

        return render_template(
            "student_dashboard.html",

            total_classes=stats[
                "total_classes"
            ],

            present_count=stats[
                "present_count"
            ],

            absent_count=stats[
                "absent_count"
            ],

            attendance_percentage=stats[
                "attendance_percentage"
            ],

            recent_attendance=recent_attendance,

            leave_requests=leave_requests
        )

    except mysql.connector.Error as e:

        print(
            "Student Dashboard MySQL Error:",
            e
        )

        flash(
            "Unable to load attendance data.",
            "error"
        )

        return render_template(
            "student_dashboard.html",

            total_classes=0,
            present_count=0,
            absent_count=0,
            attendance_percentage=0,
            recent_attendance=[],
            leave_requests=[]
        )

    except Exception as e:

        print(
            "Student Dashboard Error:",
            e
        )

        flash(
            "Something went wrong while loading dashboard.",
            "error"
        )

        return render_template(
            "student_dashboard.html",

            total_classes=0,
            present_count=0,
            absent_count=0,
            attendance_percentage=0,
            recent_attendance=[],
            leave_requests=[]
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# FACE ATTENDANCE
# =========================================================

@app.route("/student/face-attendance")
def face_attendance():

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    # =====================================================
    # ATTENDANCE TIME CHECK
    # =====================================================

    if not is_attendance_time_allowed():

        flash(
            "Attendance marking is allowed only from 10:00 AM to 3:00 PM.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    try:

        result = recognize_student(
            student_id
        )

    except Exception as e:

        print(
            "Face Recognition Error:",
            e
        )

        flash(
            "Unable to start face recognition.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    if not result.get(
        "success",
        False
    ):

        flash(
            result.get(
                "message",
                "Face not recognized."
            ),
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    recognized_id = str(
        result.get(
            "student_id",
            ""
        )
    )

    if recognized_id != str(student_id):

        flash(
            "Face belongs to another student.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        check_query = """
            SELECT
                id,
                status
            FROM attendance
            WHERE student_id = %s
              AND attendance_date = CURDATE()
            LIMIT 1
        """

        cursor.execute(
            check_query,
            (student_id,)
        )

        existing = cursor.fetchone()

        if existing:

            flash(
                "Your attendance is already marked for today.",
                "error"
            )

            return redirect(
                url_for("student_dashboard")
            )

        insert_query = """
            INSERT INTO attendance
            (
                student_id,
                attendance_date,
                attendance_time,
                method,
                status
            )
            VALUES
            (
                %s,
                CURDATE(),
                CURTIME(),
                %s,
                %s
            )
        """

        cursor.execute(
            insert_query,
            (
                student_id,
                "FACE",
                "PRESENT"
            )
        )

        connection.commit()

        stats = get_attendance_statistics(
            student_id
        )

        flash(
            f"Attendance marked successfully! "
            f"Attendance: "
            f"{stats['attendance_percentage']:.2f}%",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Face Attendance MySQL Error:",
            e
        )

        flash(
            "Unable to save attendance.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Face Attendance Error:",
            e
        )

        flash(
            "Something went wrong while marking attendance.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# TEST ABSENT
# =========================================================

@app.route("/student/test-absent")
def test_absent():

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        check_query = """
            SELECT id
            FROM attendance
            WHERE student_id = %s
              AND attendance_date = CURDATE()
            LIMIT 1
        """

        cursor.execute(
            check_query,
            (student_id,)
        )

        existing = cursor.fetchone()

        if existing:

            flash(
                "Attendance record already exists for today.",
                "error"
            )

            return redirect(
                url_for("student_dashboard")
            )

        insert_query = """
            INSERT INTO attendance
            (
                student_id,
                attendance_date,
                attendance_time,
                method,
                status
            )
            VALUES
            (
                %s,
                CURDATE(),
                CURTIME(),
                %s,
                %s
            )
        """

        cursor.execute(
            insert_query,
            (
                student_id,
                "SYSTEM",
                "ABSENT"
            )
        )

        connection.commit()

        flash(
            "Test ABSENT record created successfully.",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Test Absent MySQL Error:",
            e
        )

        flash(
            "Unable to create absent record.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Test Absent Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# SUBMIT LEAVE REQUEST
# =========================================================

@app.route(
    "/student/leave",
    methods=["POST"]
)
def submit_leave():

    if "student_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    student_id = session["student_id"]

    from_date = request.form.get(
        "from_date",
        ""
    ).strip()

    to_date = request.form.get(
        "to_date",
        ""
    ).strip()

    reason = request.form.get(
        "reason",
        ""
    ).strip()

    if not from_date:

        flash(
            "From Date is required.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    if not to_date:

        flash(
            "To Date is required.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    if not reason:

        flash(
            "Leave reason is required.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    if to_date < from_date:

        flash(
            "To Date cannot be before From Date.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO leave_requests
            (
                student_id,
                from_date,
                to_date,
                reason,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        cursor.execute(
            query,
            (
                student_id,
                from_date,
                to_date,
                reason,
                "PENDING"
            )
        )

        connection.commit()

        flash(
            "Leave request submitted successfully!",
            "success"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Leave MySQL Error:",
            e
        )

        flash(
            "Unable to submit leave request.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Leave Request Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# TEACHER REGISTRATION
# =========================================================

@app.route(
    "/teacher/register",
    methods=["GET", "POST"]
)
def teacher_register():

    if request.method == "GET":

        return render_template(
            "teacher_register.html"
        )

    teacher_id = request.form.get(
        "teacher_id",
        ""
    ).strip()

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()

    if not teacher_id:

        flash(
            "Teacher ID is required.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    if not name:

        flash(
            "Teacher name is required.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    if not email:

        flash(
            "Email is required.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    if not password:

        flash(
            "Password is required.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    if len(password) < 6:

        flash(
            "Password must be at least 6 characters.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    if password != confirm_password:

        flash(
            "Passwords do not match.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    hashed_password = generate_password_hash(
        password
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO teachers
            (
                teacher_id,
                name,
                email,
                password
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
        """

        cursor.execute(
            query,
            (
                teacher_id,
                name,
                email,
                hashed_password
            )
        )

        connection.commit()

        flash(
            "Teacher account created successfully! You can now login.",
            "success"
        )

        return redirect(
            url_for("home")
        )

    except mysql.connector.IntegrityError as e:

        if connection:
            connection.rollback()

        print(
            "Teacher Duplicate Error:",
            e
        )

        flash(
            "Teacher ID or Email already exists.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Teacher MySQL Error:",
            e
        )

        flash(
            "Database error occurred.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Teacher Registration Error:",
            e
        )

        flash(
            "Something went wrong.",
            "error"
        )

        return redirect(
            url_for("teacher_register")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# =========================================================
# TEACHER ATTENDANCE REGISTER
# =========================================================

@app.route("/teacher/attendance")
def teacher_attendance():

    # -----------------------------------------------------
    # CHECK TEACHER LOGIN
    # -----------------------------------------------------

    if "teacher_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    connection = None
    cursor = None

    # -----------------------------------------------------
    # SELECTED DATE
    # -----------------------------------------------------

    selected_date = request.args.get(
        "date",
        ""
    ).strip()

    if not selected_date:

        # MySQL server date
        selected_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

    # -----------------------------------------------------
    # DEFAULT VALUES
    # -----------------------------------------------------

    attendance_records = []

    total_students = 0
    present_count = 0
    absent_count = 0
    attendance_percentage = 0.0

    try:

        # -------------------------------------------------
        # DATABASE CONNECTION
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # 1. TOTAL STUDENTS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total_students
            FROM students
            WHERE UPPER(TRIM(status)) = 'ACTIVE'
            """
        )

        result = cursor.fetchone()

        total_students = int(
            (result or {}).get(
                "total_students",
                0
            ) or 0
        )

        # =================================================
        # 2. ATTENDANCE REGISTER
        #
        # Every active student is displayed.
        #
        # If attendance exists:
        #     use PRESENT / ABSENT record
        #
        # If attendance does not exist:
        #     automatically show ABSENT
        # =================================================

        query = """
        SELECT

            s.student_id,

            s.name,

            s.roll_number,

            %s AS attendance_date,

            COALESCE(
                a.attendance_time,
                NULL
            ) AS attendance_time,

            COALESCE(
                a.method,
                'SYSTEM'
            ) AS method,

            CASE

                WHEN a.student_id IS NULL
                THEN 'ABSENT'

                ELSE UPPER(
                    TRIM(a.status)
                )

            END AS status,

            CASE

                WHEN stats.total_classes > 0

                THEN ROUND(
                    (
                        stats.present_classes
                        /
                        stats.total_classes
                    ) * 100,
                    2
                )

                ELSE 0

            END AS attendance_percentage

        FROM students s

        LEFT JOIN (

            SELECT
                a1.student_id,
                a1.attendance_date,
                a1.attendance_time,
                a1.method,
                a1.status

            FROM attendance a1

            LEFT JOIN attendance a2

                ON a2.student_id =
                   a1.student_id

                AND a2.attendance_date =
                    a1.attendance_date

                AND (

                    (
                        UPPER(
                            TRIM(a2.status)
                        ) = 'PRESENT'

                        AND UPPER(
                            TRIM(a1.status)
                        ) <> 'PRESENT'
                    )

                    OR

                    (
                        UPPER(
                            TRIM(a2.status)
                        )
                        =
                        UPPER(
                            TRIM(a1.status)
                        )

                        AND a2.attendance_time
                            > a1.attendance_time
                    )

                )

            WHERE a2.id IS NULL

        ) a

            ON a.student_id =
               s.student_id

            AND a.attendance_date =
                %s

        LEFT JOIN (

            SELECT

                student_id,

                COUNT(*) AS total_classes,

                SUM(
                    CASE

                        WHEN UPPER(
                            TRIM(status)
                        ) = 'PRESENT'

                        THEN 1

                        ELSE 0

                    END
                ) AS present_classes

            FROM attendance

            GROUP BY student_id

        ) stats

            ON stats.student_id =
               s.student_id

        WHERE UPPER(
            TRIM(s.status)
        ) = 'ACTIVE'

        ORDER BY
            s.student_id ASC
        """

        cursor.execute(
            query,
            (
                selected_date,
                selected_date
            )
        )

        attendance_records = (
            cursor.fetchall()
        )

        # =================================================
        # 3. PRESENT COUNT
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(DISTINCT student_id)
            AS present_count

            FROM attendance

            WHERE attendance_date = %s

            AND UPPER(
                TRIM(status)
            ) = 'PRESENT'
            """,
            (
                selected_date,
            )
        )

        result = cursor.fetchone()

        present_count = int(
            (result or {}).get(
                "present_count",
                0
            ) or 0
        )

        # =================================================
        # 4. ABSENT COUNT
        # =================================================

        absent_count = max(
            total_students - present_count,
            0
        )

        # =================================================
        # 5. OVERALL ATTENDANCE %
        # =================================================

        if total_students > 0:

            attendance_percentage = round(
                (
                    present_count
                    /
                    total_students
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0.0

        # =================================================
        # DEBUG
        # =================================================

        print()
        print(
            "========================================"
        )

        print(
            "TEACHER ATTENDANCE REGISTER"
        )

        print(
            "Teacher ID:",
            session.get("teacher_id")
        )

        print(
            "Selected Date:",
            selected_date
        )

        print(
            "Total Students:",
            total_students
        )

        print(
            "Present:",
            present_count
        )

        print(
            "Absent:",
            absent_count
        )

        print(
            "Attendance:",
            attendance_percentage,
            "%"
        )

        print(
            "========================================"
        )

        # =================================================
        # RENDER PAGE
        # =================================================

        return render_template(
            "teacher_attendance.html",

            attendance_records=
                attendance_records,

            selected_date=
                selected_date,

            total_students=
                total_students,

            present_count=
                present_count,

            absent_count=
                absent_count,

            attendance_percentage=
                attendance_percentage
        )

    # -----------------------------------------------------
    # MYSQL ERROR
    # -----------------------------------------------------

    except mysql.connector.Error as e:

        print(
            "Teacher Attendance MySQL Error:",
            e
        )

        flash(
            "Unable to load attendance.",
            "error"
        )

        return render_template(
            "teacher_attendance.html",

            attendance_records=[],

            selected_date=
                selected_date,

            total_students=0,

            present_count=0,

            absent_count=0,

            attendance_percentage=0.0
        )

    # -----------------------------------------------------
    # GENERAL ERROR
    # -----------------------------------------------------

    except Exception as e:

        print(
            "Teacher Attendance Error:",
            e
        )

        flash(
            "Something went wrong while loading attendance.",
            "error"
        )

        return render_template(
            "teacher_attendance.html",

            attendance_records=[],

            selected_date=
                selected_date,

            total_students=0,

            present_count=0,

            absent_count=0,

            attendance_percentage=0.0
        )

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()

# =========================================================
# TEACHER DASHBOARD
# =========================================================

@app.route("/teacher/dashboard")
def teacher_dashboard():

    # -----------------------------------------------------
    # CHECK TEACHER LOGIN
    # -----------------------------------------------------

    if "teacher_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # -----------------------------------------------------
    # STUDENT ID FILTER
    # -----------------------------------------------------

    selected_student_id = request.args.get(
        "student_id",
        ""
    ).strip()

    connection = None
    cursor = None

    # -----------------------------------------------------
    # DEFAULT VALUES
    # -----------------------------------------------------

    leave_requests = []
    students = []
    attendance_records = []

    total_students = 0
    present_today = 0
    absent_today = 0
    attendance_percentage = 0.0

    try:

        # =================================================
        # DATABASE CONNECTION
        # =================================================

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # 1. LOAD STUDENTS
        # =================================================

        try:

            cursor.execute("""
                SELECT
                    student_id,
                    name,
                    roll_number,
                    email,
                    department,
                    year,
                    status
                FROM students
                ORDER BY student_id DESC
            """)

            students = cursor.fetchall()

        except mysql.connector.Error as e:

            print(
                "Teacher Students Query Error:",
                e
            )

            students = []

        # =================================================
        # 2. LOAD LEAVE REQUESTS
        # =================================================

        try:

            cursor.execute("""
                SELECT
                    id,
                    student_id,
                    from_date,
                    to_date,
                    reason,
                    status
                FROM leave_requests
                ORDER BY
                    CASE
                        WHEN UPPER(TRIM(status)) = 'PENDING'
                        THEN 1

                        WHEN UPPER(TRIM(status)) = 'APPROVED'
                        THEN 2

                        WHEN UPPER(TRIM(status)) = 'REJECTED'
                        THEN 3

                        ELSE 4
                    END,
                    id DESC
            """)

            leave_requests = cursor.fetchall()

            # -------------------------------------------------
            # ADD STUDENT NAME
            # -------------------------------------------------

            for leave in leave_requests:

                student_id = leave.get(
                    "student_id"
                )

                leave["student_name"] = (
                    "Student " + str(student_id)
                    if student_id is not None
                    else "Unknown Student"
                )

                try:

                    student_cursor = connection.cursor(
                        dictionary=True
                    )

                    student_cursor.execute(
                        """
                        SELECT name
                        FROM students
                        WHERE student_id = %s
                        LIMIT 1
                        """,
                        (student_id,)
                    )

                    student = student_cursor.fetchone()

                    if student and student.get("name"):

                        leave["student_name"] = (
                            student["name"]
                        )

                    student_cursor.close()

                except mysql.connector.Error as e:

                    print(
                        "Student Name Query Error:",
                        e
                    )

        except mysql.connector.Error as e:

            print(
                "Teacher Leave Query Error:",
                e
            )

            leave_requests = []

        # =================================================
        # 3. LOAD ATTENDANCE RECORDS
        # =================================================

        try:

            attendance_query = """
                SELECT
                    a.student_id,
                    s.name AS name,
                    a.attendance_date AS date,
                    a.attendance_time AS time,
                    a.method,
                    a.status

                FROM attendance a

                LEFT JOIN students s
                    ON a.student_id = s.student_id

                WHERE 1 = 1
            """

            attendance_params = []

            # -------------------------------------------------
            # STUDENT ID FILTER
            # -------------------------------------------------

            if selected_student_id:

                attendance_query += """
                    AND a.student_id = %s
                """

                attendance_params.append(
                    selected_student_id
                )

            # -------------------------------------------------
            # ORDER RECORDS
            # -------------------------------------------------

            attendance_query += """
                ORDER BY
                    a.attendance_date DESC,
                    a.attendance_time DESC

                LIMIT 100
            """

            cursor.execute(
                attendance_query,
                tuple(attendance_params)
            )

            attendance_records = cursor.fetchall()

        except mysql.connector.Error as e:

            print(
                "Teacher Attendance Query Error:",
                e
            )

            attendance_records = []

        # =================================================
        # 4. TOTAL STUDENTS
        # =================================================

        try:

            cursor.execute("""
                SELECT COUNT(*) AS total_students
                FROM students
            """)

            result = cursor.fetchone()

            if result:

                total_students = int(
                    result.get(
                        "total_students",
                        0
                    ) or 0
                )

        except mysql.connector.Error as e:

            print(
                "Total Students Query Error:",
                e
            )

            total_students = len(
                students
            )

        # =================================================
        # 5. PRESENT TODAY
        # =================================================

        try:

            cursor.execute("""
                SELECT COUNT(*) AS present_today
                FROM attendance
                WHERE attendance_date = CURDATE()
                  AND UPPER(TRIM(status)) = 'PRESENT'
            """)

            result = cursor.fetchone()

            if result:

                present_today = int(
                    result.get(
                        "present_today",
                        0
                    ) or 0
                )

        except mysql.connector.Error as e:

            print(
                "Present Today Query Error:",
                e
            )

            present_today = 0

        # =================================================
        # 6. ABSENT TODAY
        # =================================================

        try:

            cursor.execute("""
                SELECT COUNT(*) AS absent_today
                FROM attendance
                WHERE attendance_date = CURDATE()
                  AND UPPER(TRIM(status)) = 'ABSENT'
            """)

            result = cursor.fetchone()

            if result:

                absent_today = int(
                    result.get(
                        "absent_today",
                        0
                    ) or 0
                )

        except mysql.connector.Error as e:

            print(
                "Absent Today Query Error:",
                e
            )

            absent_today = 0

        # =================================================
        # 7. ATTENDANCE PERCENTAGE
        # =================================================

        attendance_total = (
            present_today +
            absent_today
        )

        if attendance_total > 0:

            attendance_percentage = round(
                (
                    present_today /
                    attendance_total
                ) * 100,
                2
            )

        else:

            attendance_percentage = 0.0

        # =================================================
        # 8. DEBUG INFORMATION
        # =================================================

        print()

        print(
            "========================================"
        )

        print(
            "TEACHER DASHBOARD LOADED"
        )

        print(
            "Teacher ID:",
            session.get("teacher_id")
        )

        print(
            "Student ID Filter:",
            selected_student_id
        )

        print(
            "Students:",
            len(students)
        )

        print(
            "Leave Requests:",
            len(leave_requests)
        )

        print(
            "Attendance Records:",
            len(attendance_records)
        )

        print(
            "========================================"
        )

        # =================================================
        # 9. RENDER DASHBOARD
        # =================================================

        return render_template(
            "teacher_dashboard.html",

            students=students,

            leave_requests=leave_requests,

            attendance_records=attendance_records,

            total_students=total_students,

            present_today=present_today,

            absent_today=absent_today,

            attendance_percentage=attendance_percentage,

            selected_student_id=selected_student_id
        )

    # =====================================================
    # MYSQL ERROR
    # =====================================================

    except mysql.connector.Error as e:

        print()

        print(
            "========================================"
        )

        print(
            "TEACHER DASHBOARD MYSQL ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "========================================"
        )

        flash(
            "Unable to load teacher dashboard.",
            "error"
        )

        return render_template(
            "teacher_dashboard.html",

            students=students,

            leave_requests=leave_requests,

            attendance_records=attendance_records,

            total_students=total_students,

            present_today=present_today,

            absent_today=absent_today,

            attendance_percentage=attendance_percentage,

            selected_student_id=selected_student_id
        )

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as e:

        print()

        print(
            "========================================"
        )

        print(
            "TEACHER DASHBOARD ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "========================================"
        )

        flash(
            "Something went wrong while loading teacher dashboard.",
            "error"
        )

        return render_template(
            "teacher_dashboard.html",

            students=students,

            leave_requests=leave_requests,

            attendance_records=attendance_records,

            total_students=total_students,

            present_today=present_today,

            absent_today=absent_today,

            attendance_percentage=attendance_percentage,

            selected_student_id=selected_student_id
        )

    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()




# =========================================================
# TEACHER ATTENDANCE REGISTER
# =========================================================

@app.route("/teacher/attendance")



# =========================================================
# FINALIZE TODAY'S ATTENDANCE
# =========================================================

@app.route("/teacher/finalize-attendance", methods=["POST"])
def finalize_attendance():

    if "teacher_id" not in session:
        flash(
            "Please login as a teacher first.",
            "error"
        )
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # TOTAL ACTIVE STUDENTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total_students
            FROM students
            WHERE UPPER(TRIM(status)) = 'ACTIVE'
        """)

        result = cursor.fetchone()

        total_students = int(
            result["total_students"] or 0
        )

        # -------------------------------------------------
        # MARK ABSENT FOR STUDENTS WHO DID NOT ATTEND
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO attendance
            (
                student_id,
                attendance_date,
                attendance_time,
                method,
                status
            )
            SELECT
                s.student_id,
                CURDATE(),
                CURTIME(),
                'SYSTEM',
                'ABSENT'
            FROM students s
            WHERE UPPER(TRIM(s.status)) = 'ACTIVE'

              AND NOT EXISTS
              (
                  SELECT 1
                  FROM attendance a
                  WHERE a.student_id = s.student_id
                    AND a.attendance_date = CURDATE()
              )
        """)

        absent_added = cursor.rowcount

        connection.commit()

        # -------------------------------------------------
        # TODAY'S FINAL STATISTICS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(status)) = 'PRESENT'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS present_today,

                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(status)) = 'ABSENT'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS absent_today

            FROM attendance
            WHERE attendance_date = CURDATE()
        """)

        stats = cursor.fetchone()

        present_today = int(
            stats["present_today"] or 0
        )

        absent_today = int(
            stats["absent_today"] or 0
        )

        attendance_percentage = (
            (present_today / total_students) * 100
            if total_students > 0
            else 0
        )

        # -------------------------------------------------
        # DEBUG
        # -------------------------------------------------

        print()
        print("========================================")
        print("ATTENDANCE FINALIZED")
        print("========================================")
        print("Total Students:", total_students)
        print("Present:", present_today)
        print("Absent:", absent_today)
        print(
            "Attendance:",
            round(attendance_percentage, 2),
            "%"
        )
        print("New Absent Records:", absent_added)
        print("========================================")

        flash(
            f"Attendance finalized successfully! "
            f"Present: {present_today}, "
            f"Absent: {absent_today}",
            "success"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Finalize Attendance MySQL Error:",
            e
        )

        flash(
            "Unable to finalize attendance.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Finalize Attendance Error:",
            e
        )

        flash(
            "Something went wrong while finalizing attendance.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# =========================================================
# DYNAMIC QR ATTENDANCE
# =========================================================

# Quick-development storage for active QR tokens.
# Tokens automatically expire after 120 seconds.
ACTIVE_QR_TOKENS = {}
QR_EXPIRY_SECONDS = 120


@app.route("/teacher/generate-qr", methods=["POST"])
def generate_qr():
    """Generate a temporary QR code for student attendance."""

    if "teacher_id" not in session:
        return {
            "success": False,
            "message": "Please login as a teacher first."
        }, 401

    if qrcode is None:
        return {
            "success": False,
            "message": "QR package is not installed. Run: pip install qrcode[pil]"
        }, 500

    try:
        # Remove expired tokens.
        now = datetime.now()
        expired = [
            token for token, info in ACTIVE_QR_TOKENS.items()
            if info["expires_at"] <= now
        ]
        for token in expired:
            ACTIVE_QR_TOKENS.pop(token, None)

        token = uuid.uuid4().hex
        expires_at = now + timedelta(seconds=QR_EXPIRY_SECONDS)

        ACTIVE_QR_TOKENS[token] = {
            "teacher_id": str(session["teacher_id"]),
            "created_at": now,
            "expires_at": expires_at
        }

        attendance_url = request.host_url.rstrip("/") + url_for(
            "qr_attendance",
            token=token
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )
        qr.add_data(attendance_url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        qr_image = (
            "data:image/png;base64,"
            + base64.b64encode(buffer.getvalue()).decode("utf-8")
        )

        return {
            "success": True,
            "qr_image": qr_image,
            "expires_in": QR_EXPIRY_SECONDS,
            "message": "Students can scan this QR code to mark attendance."
        }

    except Exception as e:
        print("Generate QR Error:", e)
        return {
            "success": False,
            "message": "Unable to generate QR code."
        }, 500


@app.route("/student/qr-attendance/<token>", methods=["GET"])
def qr_attendance(token):
    """Mark the logged-in student present using a valid temporary QR token."""

    if "student_id" not in session:
        flash("Please login as a student before scanning the attendance QR.", "error")
        return redirect(url_for("home"))

    # =====================================================
    # ATTENDANCE TIME CHECK
    # =====================================================

    if not is_attendance_time_allowed():

        flash(
            "Attendance marking is allowed only from 10:00 AM to 3:00 PM.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    token = str(token).strip()
    qr_info = ACTIVE_QR_TOKENS.get(token)

    if qr_info is None:
        flash("This QR code is invalid or has expired.", "error")
        return redirect(url_for("student_dashboard"))

    if qr_info["expires_at"] <= datetime.now():
        ACTIVE_QR_TOKENS.pop(token, None)
        flash("This QR code has expired. Ask the teacher to generate a new one.", "error")
        return redirect(url_for("student_dashboard"))

    student_id = str(session["student_id"])
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Prevent duplicate attendance for the same student on the same day.
        cursor.execute(
            """
            SELECT id
            FROM attendance
            WHERE student_id = %s
              AND attendance_date = CURDATE()
            LIMIT 1
            """,
            (student_id,)
        )

        if cursor.fetchone():
            flash("Your attendance is already marked for today.", "error")
            return redirect(url_for("student_dashboard"))

        cursor.execute(
            """
            INSERT INTO attendance
            (student_id, attendance_date, attendance_time, method, status)
            VALUES (%s, CURDATE(), CURTIME(), %s, %s)
            """,
            (student_id, "QR", "PRESENT")
        )

        connection.commit()

        flash("Attendance marked successfully using QR code!", "success")
        return redirect(url_for("student_dashboard"))

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        print("QR Attendance MySQL Error:", e)
        flash("Unable to save QR attendance.", "error")
        return redirect(url_for("student_dashboard"))

    except Exception as e:
        if connection:
            connection.rollback()
        print("QR Attendance Error:", e)
        flash("Something went wrong while marking QR attendance.", "error")
        return redirect(url_for("student_dashboard"))

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("home")
    )

 # =========================================================
# TEACHER APPROVE LEAVE REQUEST
# =========================================================

@app.route(
    "/teacher/leave/<int:leave_id>/approve",
    methods=["POST"]
)
def approve_leave(leave_id):

    if "teacher_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            UPDATE leave_requests
            SET status = %s
            WHERE id = %s
              AND UPPER(TRIM(status)) = 'PENDING'
        """

        cursor.execute(
            query,
            (
                "APPROVED",
                leave_id
            )
        )

        if cursor.rowcount == 0:

            connection.rollback()

            flash(
                "Leave request was not found or has already been processed.",
                "error"
            )

        else:

            connection.commit()

            flash(
                "Leave request approved successfully.",
                "success"
            )

        return redirect(
            url_for("teacher_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Approve Leave MySQL Error:",
            e
        )

        flash(
            "Unable to approve leave request.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Approve Leave Error:",
            e
        )

        flash(
            "Something went wrong while approving the leave request.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# TEACHER REJECT LEAVE REQUEST
# =========================================================

@app.route(
    "/teacher/leave/<int:leave_id>/reject",
    methods=["POST"]
)
def reject_leave(leave_id):

    if "teacher_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            UPDATE leave_requests
            SET status = %s
            WHERE id = %s
              AND UPPER(TRIM(status)) = 'PENDING'
        """

        cursor.execute(
            query,
            (
                "REJECTED",
                leave_id
            )
        )

        if cursor.rowcount == 0:

            connection.rollback()

            flash(
                "Leave request was not found or has already been processed.",
                "error"
            )

        else:

            connection.commit()

            flash(
                "Leave request rejected successfully.",
                "success"
            )

        return redirect(
            url_for("teacher_dashboard")
        )

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print(
            "Reject Leave MySQL Error:",
            e
        )

        flash(
            "Unable to reject leave request.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "Reject Leave Error:",
            e
        )

        flash(
            "Something went wrong while rejecting the leave request.",
            "error"
        )

        return redirect(
            url_for("teacher_dashboard")
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("SVM SMART ATTENDANCE SYSTEM")
    print("========================================")
    print()
    print("Server started successfully!")
    print()
    print("Local:")
    print("http://127.0.0.1:5000")
    print()
    print("Network:")
    print("http://10.71.48.31:5000")
    print()
    print("========================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )