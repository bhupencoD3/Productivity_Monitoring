import cv2
from face_recognition.detection import StableEyeDetector
# from face_recognition.recognition import FaceRecognizer


def main():
    detector = StableEyeDetector()
    cap = cv2.VideoCapture(0)

    # Set optimal camera parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        ear, state, landmarks = detector.process_frame(frame)

        # Display information
        text = f"State: {state}"
        color = (
            (0, 255, 0)
            if state == "open"
            else (0, 0, 255)
            if state == "closed"
            else (0, 255, 255)
        )

        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Show calibration progress
        if not detector.calibrated:
            progress = min(len(detector.ear_window) / detector.calibration_frames, 1.0)
            cv2.rectangle(frame, (10, 40), (210, 50), (50, 50, 50), -1)
            cv2.rectangle(
                frame, (10, 40), (10 + int(200 * progress), 50), (0, 255, 0), -1
            )

        cv2.imshow("Eye State Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
