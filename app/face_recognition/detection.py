# face_recognition/detection.py
import cv2
import numpy as np
from scipy.signal import savgol_filter
from collections import deque
import mediapipe as mp
import datetime
import logging

logging.getLogger("mediapipe").setLevel(logging.ERROR)

class ProductivityEyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4,
        )
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.current_state = "open"
        self.state_start_time = datetime.datetime.now()
        self.closed_duration_threshold = 2.0
        self.min_closed_frames = 30
        self.closed_frame_count = 0
        self.total_closed_time = 0.0
        self.log_buffer = []
        self.ear_threshold = 0.23
        self.state_history = deque(maxlen=20)

    def calculate_ear(self, landmarks):
        try:
            def eye_aspect_ratio(eye_indices):
                coords = [(landmarks[i].x, landmarks[i].y) for i in eye_indices]
                vertical1 = np.linalg.norm(np.subtract(coords[1], coords[5]))
                vertical2 = np.linalg.norm(np.subtract(coords[2], coords[4]))
                horizontal = np.linalg.norm(np.subtract(coords[0], coords[3]))
                return (vertical1 + vertical2) / (2.0 * horizontal + 1e-6)

            ear = (eye_aspect_ratio(self.LEFT_EYE) + eye_aspect_ratio(self.RIGHT_EYE)) / 2
            return ear
        except Exception as e:
            print(f"EAR calculation error: {str(e)}")
            return None

    def process_frame(self, frame):
        results = self.mp_face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        current_time = datetime.datetime.now()

        if not results.multi_face_landmarks:
            if self.current_state == "closed" and self.closed_frame_count >= self.min_closed_frames:
                duration = (current_time - self.state_start_time).total_seconds()
                if duration >= self.closed_duration_threshold:
                    self.log_buffer.append({
                        "start": self.state_start_time,
                        "end": current_time,
                        "duration": duration
                    })
                    self.total_closed_time += duration
                    self.closed_frame_count = 0
            self.current_state = None
            self.state_history.clear()
            print(f"No face detected at {current_time}")
            return None

        landmarks = results.multi_face_landmarks[0].landmark
        ear = self.calculate_ear(landmarks)
        if ear is None:
            self.current_state = None
            self.closed_frame_count = 0
            self.state_history.clear()
            print(f"EAR is None at {current_time}")
            return None

        self.state_history.append(ear)
        print(f"EAR: {ear:.3f}, History length: {len(self.state_history)}")

        if len(self.state_history) >= 15:
            smoothed_ear = savgol_filter(self.state_history, 15, 2)[-1]
            new_state = "open" if smoothed_ear > self.ear_threshold else "closed"
            print(f"Smoothed EAR: {smoothed_ear:.3f}, New state: {new_state}")

            if new_state == "closed":
                self.closed_frame_count += 1
                if self.current_state != "closed":
                    self.current_state = "closed"
                    self.state_start_time = current_time
                elif self.closed_frame_count >= self.min_closed_frames:
                    duration = (current_time - self.state_start_time).total_seconds()
                    if duration >= self.closed_duration_threshold:
                        self.log_buffer.append({
                            "start": self.state_start_time,
                            "end": current_time,
                            "duration": duration
                        })
                        self.total_closed_time += duration
                        self.state_start_time = current_time
                        self.closed_frame_count = 0
            else:
                if self.current_state == "closed" and self.closed_frame_count >= self.min_closed_frames:
                    duration = (current_time - self.state_start_time).total_seconds()
                    if duration >= self.closed_duration_threshold:
                        self.log_buffer.append({
                            "start": self.state_start_time,
                            "end": current_time,
                            "duration": duration
                        })
                        self.total_closed_time += duration
                        self.closed_frame_count = 0
                self.current_state = "open"
                self.state_start_time = current_time if self.current_state != "open" else self.state_start_time
        else:
            self.current_state = "open"

        return self.current_state

    def get_productivity_stats(self):
        return {
            "current_state": self.current_state,
            "total_closed": self.total_closed_time,
            "state_since": self.state_start_time,
            "pending_logs": self.log_buffer.copy(),
        }

    def clear_log_buffer(self):
        self.log_buffer.clear()
