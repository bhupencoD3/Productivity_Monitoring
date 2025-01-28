import cv2
import mediapipe as mp
import numpy as np


class FaceMeshDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

    def calculate_ear(self, landmarks, left_eye_indices, right_eye_indices):
        left_eye = [landmarks[i] for i in left_eye_indices]
        left_vertical = np.linalg.norm(left_eye[1] - left_eye[5]) + np.linalg.norm(
            left_eye[2] - left_eye[4]
        )
        left_horizontal = np.linalg.norm(left_eye[0] - left_eye[3])
        left_ear = left_vertical / (2.0 * left_horizontal)

        right_eye = [landmarks[i] for i in right_eye_indices]
        right_vertical = np.linalg.norm(right_eye[1] - right_eye[5]) + np.linalg.norm(
            right_eye[2] - right_eye[4]
        )
        right_horizontal = np.linalg.norm(right_eye[0] - right_eye[3])
        right_ear = right_vertical / (2.0 * right_horizontal)

        return (left_ear + right_ear) / 2.0

    def detect_eye_status(self, frame):
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = np.array([[lm.x, lm.y] for lm in face_landmarks.landmark])
                ear = self.calculate_ear(
                    landmarks, self.LEFT_EYE_INDICES, self.RIGHT_EYE_INDICES
                )
                return ear, landmarks
        return None, None

    def draw_eye_landmarks(self, frame, landmarks):
        for index in self.LEFT_EYE_INDICES + self.RIGHT_EYE_INDICES:
            x = int(landmarks[index][0] * frame.shape[1])
            y = int(landmarks[index][1] * frame.shape[0])
            cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)  # Draw eye landmarks in red
