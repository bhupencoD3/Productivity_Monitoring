import cv2
from face_recognition.detection import FaceMeshDetector
from face_recognition.recognition import FaceRecognizer


def main():
    # Initialize the face mesh detector and face recognizer
    face_mesh_detector = FaceMeshDetector(min_detection_confidence=0.5)
    face_recognizer = FaceRecognizer()

    # Load known faces and names
    known_faces = [
        "/home/bhupen/Downloads/bhupendra.jpeg",  # Replace with the correct paths
        "/home/bhupen/Downloads/shubham.jpeg",
    ]
    known_names = ["bhupen", "Shubham"]  # Replace with the correct names
    face_recognizer.load_known_faces(known_faces, known_names)

    # EAR threshold for eye status
    EAR_THRESHOLD = 0.3

    # Start video capture
    cap = cv2.VideoCapture(0)  # 0 for the default webcam

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read from the camera.")
            break

        # Detect eye status and landmarks
        ear, landmarks = face_mesh_detector.detect_eye_status(frame)
        eye_status = "Open" if ear is not None and ear > EAR_THRESHOLD else "Closed"

        # Perform face recognition
        name = "No face detected"
        if ear is not None:
            name = face_recognizer.recognize_face(frame)

        # Draw landmarks and bounding boxes
        if landmarks is not None:
            face_mesh_detector.draw_eye_landmarks(frame, landmarks)

        # Display the recognized name and eye status
        cv2.putText(
            frame,
            f"{name} | Eye: {eye_status}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Show the frame
        cv2.imshow("Face Recognition and Eye Status", frame)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
