import cv2
import os
import datetime
from face_recognition.recognition import ProductivityRecognizer
from face_recognition.detection import ProductivityEyeTracker
from threading import Thread


def setup_logging(user_id):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(
        log_dir,
        f"productivity_{user_id}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
    )
    with open(log_filename, "w") as f:
        f.write(f"Productivity Report for {user_id}\n")
        f.write(
            f"Monitoring started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
    return log_filename


def async_log_writer(log_file, entries):
    with open(log_file, "a") as f:
        for entry in entries:
            log_line = (
                f"Closed Period: {entry['start'].strftime('%H:%M:%S')} - "
                f"{entry['end'].strftime('%H:%M:%S')} ({entry['duration']:.1f}s)"
            )
            f.write(log_line + "\n")


def recognize_user(recognizer, cap, timeout=20):
    start_time = datetime.datetime.now()
    frame_count = 0
    frame_skip = 2
    while (datetime.datetime.now() - start_time).seconds < timeout:
        ret, frame = cap.read()
        if not ret:
            return False
        frame_count += 1
        if frame_count % frame_skip == 0:
            print(f"Attempting recognition on frame {frame_count}...")
            if recognizer.recognize_user(frame):
                cv2.destroyWindow("Detected Face 0")  # Close debug window
                return True
        frame_display = frame.copy()
        cv2.putText(
            frame_display,
            "Face the camera for identification",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame_display,
            f"Time remaining: {timeout - (datetime.datetime.now() - start_time).seconds}s",
            (50, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            1,
        )
        cv2.imshow("Productivity Monitor", frame_display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return False
    return False


def main():
    os.makedirs("known_faces", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    BASE_PATH = "/home/bhupen/Productivity_tracker_edited/pRODUCTIVITY-mONITORING/app/known_faces"
    KNOWN_FACES = [
        ("bhupen", os.path.join(BASE_PATH, "bhupend.jpeg")),
        ("tushar", os.path.join(BASE_PATH, "2025-01-31_11_09_17.jpg")),
        ("bhupendra", os.path.join(BASE_PATH, "bhupendra.jpeg")),
    ]

    for name, path in KNOWN_FACES:
        if not os.path.exists(path):
            print(f"Error: File does not exist: {path}")
            return

    recognizer = ProductivityRecognizer(KNOWN_FACES)
    if not recognizer.known_embeddings:
        print("No known faces loaded successfully. Exiting...")
        return

    eye_tracker = ProductivityEyeTracker()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print("Camera initialized successfully")

    # State variables
    state = "recognition"  # Start in recognition mode
    user_id = None
    log_file = None
    frame_count = 0
    PROCESS_EVERY_NTH_FRAME = 4
    last_display_text = ""

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            frame_count += 1
            frame_display = frame.copy()

            if state == "recognition":
                if recognize_user(recognizer, cap, timeout=20 if not user_id else 10):
                    user_id = recognizer.get_identity()
                    if log_file is None or user_id != recognizer.get_identity():
                        log_file = setup_logging(user_id)
                    print(f"Transitioning to monitoring for {user_id}...")
                    frame_display = frame.copy()
                    cv2.putText(
                        frame_display,
                        f"Starting monitoring for {user_id}...",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
                    cv2.imshow("Productivity Monitor", frame_display)
                    cv2.waitKey(200)
                    state = "monitoring"
                    frame_count = 0  # Reset for monitoring
                else:
                    print("Recognition failed or user quit.")
                    break

            elif state == "monitoring":
                if frame_count % PROCESS_EVERY_NTH_FRAME == 0:
                    scale_factor = 0.5
                    small_frame = cv2.resize(
                        frame, (0, 0), fx=scale_factor, fy=scale_factor
                    )
                    eye_state = eye_tracker.process_frame(small_frame)
                    stats = eye_tracker.get_productivity_stats()

                    if eye_state is None:  # No face detected
                        if "no_face_start" not in locals():
                            no_face_start = datetime.datetime.now()
                        elif (datetime.datetime.now() - no_face_start).seconds >= 2:
                            print(
                                "No face detected for 2 seconds. Switching back to recognition..."
                            )
                            state = "recognition"
                            frame_display = frame.copy()
                            cv2.putText(
                                frame_display,
                                "No face detected. Please face the camera.",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (0, 0, 255),
                                2,
                            )
                            cv2.imshow("Productivity Monitor", frame_display)
                            cv2.waitKey(200)
                            eye_tracker.__init__()  # Reset eye tracker stats
                            continue
                        continue
                    else:
                        if "no_face_start" in locals():
                            del no_face_start

                    display_text = "\n".join(
                        [
                            f"User: {user_id}",
                            f"State: {eye_state}",
                            f"Closed Time: {stats['total_closed']:.1f}s",
                            "Press Q to exit",
                        ]
                    )
                    cv2.rectangle(frame_display, (0, 0), (640, 80), (0, 0, 0), -1)
                    cv2.putText(
                        frame_display,
                        display_text,
                        (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        1,
                    )
                    last_display_text = display_text
                    if stats["pending_logs"]:
                        Thread(
                            target=async_log_writer,
                            args=(log_file, stats["pending_logs"]),
                        ).start()
                        eye_tracker.clear_log_buffer()
                else:
                    cv2.rectangle(frame_display, (0, 0), (640, 80), (0, 0, 0), -1)
                    cv2.putText(
                        frame_display,
                        last_display_text,
                        (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        1,
                    )

            cv2.imshow("Productivity Monitor", frame_display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if log_file:
            total_closed = eye_tracker.get_productivity_stats()["total_closed"]
            with open(log_file, "a") as f:
                f.write(
                    f"\nMonitoring ended: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"Total Closed Duration: {total_closed:.1f} seconds\n")
                f.write(
                    f"Productivity Score: {max(0, 100 - (total_closed / 3600) * 100):.1f}%"
                )


if __name__ == "__main__":
    main()

