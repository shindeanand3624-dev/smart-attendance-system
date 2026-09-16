import cv2
import face_recognition

print("OpenCV version:", cv2.__version__)
print("Face Recognition imported successfully!")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

print("Camera started.")
print("Press Q to close.")

while True:

    ret, frame = camera.read()

    if not ret:
        print("ERROR: Could not read camera.")
        break

    cv2.imshow("Face Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()