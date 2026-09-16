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

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "smart_attendance"
}


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

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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

            # -------------------------------------------------
            # ACCOUNT STATUS
            # -------------------------------------------------

            student_status = str(
                student.get("status", "ACTIVE")
            ).upper()

            if student_status != "ACTIVE":

                flash(
                    "Your student account is not active.",
                    "error"
                )

                return redirect(url_for("home"))

            # -------------------------------------------------
            # PASSWORD
            # -------------------------------------------------

            if not check_password_hash(
                student["password"],
                password
            ):

                flash(
                    "Invalid Student ID/Email or Password.",
                    "error"
                )

                return redirect(url_for("home"))

            # -------------------------------------------------
            # STUDENT SESSION
            # -------------------------------------------------

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

            # -------------------------------------------------
            # TEACHER SESSION
            # -------------------------------------------------

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

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "GET":
        return render_template("forgot_password.html")

    user_type = request.form.get("user_type", "student").strip().lower()
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not email:
        flash("Please enter your registered email.", "error")
        return redirect(url_for("forgot_password"))

    if not new_password:
        flash("Please enter a new password.", "error")
        return redirect(url_for("forgot_password"))

    if len(new_password) < 6:
        flash("Password must contain at least 6 characters.", "error")
        return redirect(url_for("forgot_password"))

    if new_password != confirm_password:
        flash("New password and confirm password do not match.", "error")
        return redirect(url_for("forgot_password"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if user_type == "student":
            cursor.execute(
                "SELECT id, student_id, email FROM students WHERE email = %s LIMIT 1",
                (email,)
            )
            user = cursor.fetchone()
            table = "students"

        elif user_type == "teacher":
            cursor.execute(
                "SELECT id, teacher_id, email FROM teachers WHERE email = %s LIMIT 1",
                (email,)
            )
            user = cursor.fetchone()
            table = "teachers"

        else:
            flash("Invalid account type.", "error")
            return redirect(url_for("forgot_password"))

        if user is None:
            flash(f"No {user_type} account found with this email.", "error")
            return redirect(url_for("forgot_password"))

        hashed_password = generate_password_hash(new_password)

        if table == "students":
            cursor.execute(
                "UPDATE students SET password = %s WHERE id = %s",
                (hashed_password, user["id"])
            )
        else:
            cursor.execute(
                "UPDATE teachers SET password = %s WHERE id = %s",
                (hashed_password, user["id"])
            )

        connection.commit()

        flash(
            f"{user_type.capitalize()} password changed successfully! Please login.",
            "success"
        )
        return redirect(url_for("home"))

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        print("Forgot Password MySQL Error:", e)
        flash("Database error occurred.", "error")
        return redirect(url_for("forgot_password"))

    except Exception as e:
        if connection:
            connection.rollback()
        print("Forgot Password Error:", e)
        flash("Something went wrong.", "error")
        return redirect(url_for("forgot_password"))

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
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

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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

        # -------------------------------------------------
        # GET ATTENDANCE STATISTICS
        # -------------------------------------------------

        stats = get_attendance_statistics(
            student_id
        )

        # -------------------------------------------------
        # DATABASE CONNECTION
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SEND DATA TO TEMPLATE
        # -------------------------------------------------

        return render_template(
            "student_dashboard.html",

            total_classes=stats["total_classes"],

            present_count=stats["present_count"],

            absent_count=stats["absent_count"],

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

    # -----------------------------------------------------
    # FACE RECOGNITION
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FACE FAILED
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VERIFY STUDENT
    # -----------------------------------------------------

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

    # =====================================================
    # DATABASE
    # =====================================================

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # CHECK TODAY ATTENDANCE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # INSERT PRESENT
        # -------------------------------------------------

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

        # -------------------------------------------------
        # UPDATED PERCENTAGE
        # -------------------------------------------------

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
# MANUAL ABSENT TEST ROUTE
#
# USE ONLY FOR TESTING
# This route creates an ABSENT record for the
# currently logged-in student.
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

        # -------------------------------------------------
        # CHECK IF TODAY ALREADY EXISTS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # INSERT ABSENT
        # -------------------------------------------------

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

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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
            "Teacher account created successfully! "
            "You can now login.",
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
# TEACHER DASHBOARD
# =========================================================

@app.route("/teacher/dashboard")
def teacher_dashboard():

    if "teacher_id" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    return render_template(
        "teacher_dashboard.html"
    )


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
    print("http://192.168.x.x:5000")
    print()
    print("========================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )