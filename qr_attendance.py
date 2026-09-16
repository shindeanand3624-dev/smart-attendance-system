import os
import uuid
from datetime import datetime, timedelta

import mysql.connector
import qrcode


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
# GENERATE QR ATTENDANCE SESSION
# =========================================================

def create_attendance_qr(base_url="http://127.0.0.1:5000"):

    connection = None
    cursor = None

    try:

        # -------------------------------------------------
        # Generate unique token
        # -------------------------------------------------

        qr_token = str(uuid.uuid4())

        # QR valid for 2 minutes
        expires_at = datetime.now() + timedelta(minutes=2)

        # -------------------------------------------------
        # Save QR session in database
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO qr_sessions
            (
                qr_token,
                expires_at,
                is_active
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
        """

        cursor.execute(
            query,
            (
                qr_token,
                expires_at,
                1
            )
        )

        connection.commit()

        # -------------------------------------------------
        # Create QR URL
        # -------------------------------------------------

        qr_url = (
            f"{base_url}/student/scan-qr"
            f"?token={qr_token}"
        )

        # -------------------------------------------------
        # QR image location
        # -------------------------------------------------

        qr_folder = os.path.join(
            "app",
            "static"
        )

        os.makedirs(
            qr_folder,
            exist_ok=True
        )

        qr_file = os.path.join(
            qr_folder,
            "attendance_qr.png"
        )

        # -------------------------------------------------
        # Generate QR image
        # -------------------------------------------------

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )

        qr.add_data(qr_url)
        qr.make(fit=True)

        image = qr.make_image()

        image.save(qr_file)

        # -------------------------------------------------
        # Return information
        # -------------------------------------------------

        return {
            "success": True,
            "token": qr_token,
            "qr_url": qr_url,
            "filename": qr_file,
            "expires_at": expires_at
        }

    except mysql.connector.Error as e:

        if connection:
            connection.rollback()

        print("QR MySQL Error:", e)

        return {
            "success": False,
            "message": "Database error while generating QR."
        }

    except Exception as e:

        if connection:
            connection.rollback()

        print("QR Generation Error:", e)

        return {
            "success": False,
            "message": "Unable to generate QR code."
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# TEST QR GENERATOR
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("SVM SMART ATTENDANCE QR GENERATOR")
    print("========================================")
    print()

    result = create_attendance_qr()

    if result["success"]:

        print("QR Code Generated Successfully!")
        print()
        print("Token:")
        print(result["token"])
        print()
        print("QR URL:")
        print(result["qr_url"])
        print()
        print("File:")
        print(result["filename"])
        print()
        print("Expires At:")
        print(result["expires_at"])
        print()

    else:

        print("QR Generation Failed!")
        print(result["message"])

    print("========================================")