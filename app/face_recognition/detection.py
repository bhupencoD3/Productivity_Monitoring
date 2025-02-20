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
        self.current_state = None
        self.last_state_change = None
        self.state_start_time = None
        self.total_closed_time = 0.0
        self.state_history = deque(maxlen=5)
        self.ear_threshold = 0.3
        self.log_buffer = []

    def calculate_ear(self, landmarks):
        try:

            def eye_aspect_ratio(eye_indices):
                coords = [(landmarks[i].x, landmarks[i].y) for i in eye_indices]
                vertical1 = np.linalg.norm(np.subtract(coords[1], coords[5]))
                vertical2 = np.linalg.norm(np.subtract(coords[2], coords[4]))
                horizontal = np.linalg.norm(np.subtract(coords[0], coords[3]))
                return (vertical1 + vertical2) / (2.0 * horizontal + 1e-6)

            return (
                eye_aspect_ratio(self.LEFT_EYE) + eye_aspect_ratio(self.RIGHT_EYE)
            ) / 2
        except Exception as e:
            print(f"EAR calculation error: {str(e)}")
            return None

    def process_frame(self, frame):
        results = self.mp_face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return None
        landmarks = results.multi_face_landmarks[0].landmark
        ear = self.calculate_ear(landmarks)
        if ear is None:
            return None
        new_state = "open" if ear > self.ear_threshold else "closed"
        self.state_history.append(ear)
        if len(self.state_history) >= 5:
            smoothed_ear = savgol_filter(self.state_history, 5, 2)[-1]
            new_state = "open" if smoothed_ear > self.ear_threshold else "closed"
        if new_state != self.current_state:
            now = datetime.datetime.now()
            if self.current_state == "closed":
                closed_duration = (now - self.state_start_time).total_seconds()
                self.total_closed_time += closed_duration
                self.log_buffer.append(
                    {
                        "start": self.state_start_time,
                        "end": now,
                        "duration": closed_duration,
                    }
                )
            self.current_state = new_state
            self.state_start_time = now
            self.last_state_change = now
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

