import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from scipy.signal import savgol_filter


class StableEyeDetector:
    def __init__(self):
        # 1. Updated to official MediaPipe eye landmarks
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]  # Right eye (user's left)
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]  # Left eye (user's right)

        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        # 2. Optimized signal processing parameters
        self.ear_window = deque(maxlen=30)  # 1-second buffer @ 30 FPS
        self.state_history = deque(maxlen=7)  # Longer confirmation buffer
        self.adaptive_threshold = 0.25
        self.state = "calibrating"
        self.calibrated = False
        self.calibration_frames = 30

        # 3. Dynamic threshold parameters
        self.ear_range = (0.15, 0.45)  # Expected EAR range

    def calculate_ear(self, landmarks):
        """Standard EAR formula with validation"""
        try:
            # Get actual landmark coordinates
            def get_coords(indices):
                return np.array([(landmarks[i][0], landmarks[i][1]) for i in indices])

            left_eye = get_coords(self.LEFT_EYE)
            right_eye = get_coords(self.RIGHT_EYE)

            # Standard EAR calculation
            def ear_calculation(eye_points):
                A = np.linalg.norm(eye_points[1] - eye_points[5])
                B = np.linalg.norm(eye_points[2] - eye_points[4])
                C = np.linalg.norm(eye_points[0] - eye_points[3])
                return (A + B) / (2.0 * C + 1e-6)

            left_ear = ear_calculation(left_eye)
            right_ear = ear_calculation(right_eye)
            return (left_ear + right_ear) / 2.0

        except Exception as e:
            print(f"EAR Error: {str(e)}")
            return None

    def smooth_signal(self, ear):
        """Two-stage filtering"""
        self.ear_window.append(ear)

        # 1. Outlier rejection
        if len(self.ear_window) > 5:
            median = np.median(self.ear_window)
            if abs(ear - median) > 0.1:  # Discard sudden jumps
                ear = median

        # 2. Double exponential smoothing
        smoothed = (
            savgol_filter(list(self.ear_window), window_length=11, polyorder=2)[-1]
            if len(self.ear_window) >= 11
            else ear
        )

        return smoothed

    def auto_calibrate(self):
        """Improved calibration with range validation"""
        if self.calibrated or len(self.ear_window) < self.calibration_frames:
            return False

        valid_ears = [
            ear
            for ear in self.ear_window
            if self.ear_range[0] < ear < self.ear_range[1]
        ]

        if not valid_ears:
            print("Calibration failed - abnormal eye states detected")
            return False

        self.adaptive_threshold = np.percentile(valid_ears, 25)  # Lower quartile
        self.calibrated = True
        print(f"Calibration Success! Threshold: {self.adaptive_threshold:.3f}")
        return True

    def determine_state(self, smoothed_ear):
        """Adaptive state machine"""
        if not self.calibrated:
            return "calibrating"

        # Dynamic hysteresis (20% of threshold)
        hysteresis = self.adaptive_threshold * 0.2
        close_thresh = self.adaptive_threshold - hysteresis
        open_thresh = self.adaptive_threshold + hysteresis

        # State transition logic
        new_state = "closed" if smoothed_ear < close_thresh else "open"

        # Require 5/7 frames confirmation
        self.state_history.append(new_state)
        if sum(s == new_state for s in self.state_history) >= 5:
            self.state = new_state

        return self.state

    def process_frame(self, frame):
        # Face detection with confidence checks
        results = self.mp_face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return None, self.state, None

        landmarks = np.array(
            [[lm.x, lm.y] for lm in results.multi_face_landmarks[0].landmark]
        )
        raw_ear = self.calculate_ear(landmarks)

        if raw_ear is None or not self.ear_range[0] < raw_ear < self.ear_range[1]:
            return None, self.state, landmarks

        smoothed_ear = self.smooth_signal(raw_ear)
        self.auto_calibrate()
        return smoothed_ear, self.determine_state(smoothed_ear), landmarks


# Usage remains the same as previous implementation

