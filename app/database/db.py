import mysql.connector

DB_CONFIG = {
"host": "localhost",
"user": "root",
"password": "",
"database": "smart_attendance"
}

print("Connecting to MySQL...")

connection = mysql.connector.connect(**DB_CONFIG)
cursor = connection.cursor()

print("MySQL connection successful!")

# ==========================================

# 1. STUDENTS TABLE

# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
id INT AUTO_INCREMENT PRIMARY KEY,
student_id VARCHAR(50) NOT NULL UNIQUE,
name VARCHAR(100) NOT NULL,
roll_number VARCHAR(50) NOT NULL UNIQUE,
email VARCHAR(100) UNIQUE,
phone VARCHAR(20),
department VARCHAR(100),
year VARCHAR(20),
face_image VARCHAR(255),
fingerprint_id VARCHAR(100),
status VARCHAR(20) DEFAULT 'ACTIVE',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("Students table created.")

# ==========================================

# 2. TEACHERS TABLE

# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
id INT AUTO_INCREMENT PRIMARY KEY,
teacher_id VARCHAR(50) NOT NULL UNIQUE,
name VARCHAR(100) NOT NULL,
email VARCHAR(100) NOT NULL UNIQUE,
password VARCHAR(255) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("Teachers table created.")

# ==========================================

# 3. ATTENDANCE TABLE

# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
id INT AUTO_INCREMENT PRIMARY KEY,
student_id VARCHAR(50) NOT NULL,
attendance_date DATE NOT NULL,
attendance_time TIME NOT NULL,
method VARCHAR(20) NOT NULL,
status VARCHAR(20) DEFAULT 'PRESENT',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("Attendance table created.")

# ==========================================

# 4. LEAVE REQUESTS TABLE

# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS leave_requests (
id INT AUTO_INCREMENT PRIMARY KEY,
student_id VARCHAR(50) NOT NULL,
from_date DATE NOT NULL,
to_date DATE NOT NULL,
reason TEXT NOT NULL,
status VARCHAR(20) DEFAULT 'PENDING',
teacher_remark TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

print("Leave requests table created.")

# ==========================================

# 5. QR SESSIONS TABLE

# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS qr_sessions (
id INT AUTO_INCREMENT PRIMARY KEY,
qr_token VARCHAR(255) NOT NULL UNIQUE,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
expires_at DATETIME NOT NULL,
is_active TINYINT(1) DEFAULT 1
)
""")

print("QR sessions table created.")

# ==========================================

# SAVE CHANGES

# ==========================================

connection.commit()

print("----------------------------------------")
print("Database initialized successfully!")
print("All tables created successfully!")
print("----------------------------------------")

# ==========================================

# CLOSE CONNECTION

# ==========================================

cursor.close()
connection.close()

print("MySQL connection closed.")
