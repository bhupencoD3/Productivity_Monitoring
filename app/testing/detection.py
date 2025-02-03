import cv2
import mediapipe as mp
import numpy as np


class EyeStateDetector:
    def __init__(self, ear_threshold=0.25):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )

        # Eye landmark indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.EAR_THRESHOLD = ear_threshold

    def calculate_ear(self, eye_landmarks):
        """Calculate Eye Aspect Ratio (EAR)"""
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        return (A + B) / (2.0 * C)

    def detect(self, frame):
        """Process frame and return results"""
        results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        output_frame = frame.copy()
        is_open = False
        openness = 0.0

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

            # Get eye landmarks
            left_eye = np.array(
                [
                    (lm.x * frame.shape[1], lm.y * frame.shape[0])
                    for lm in [face_landmarks.landmark[i] for i in self.LEFT_EYE]
                ]
            )
            right_eye = np.array(
                [
                    (lm.x * frame.shape[1], lm.y * frame.shape[0])
                    for lm in [face_landmarks.landmark[i] for i in self.RIGHT_EYE]
                ]
            )

            # Calculate EAR
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            avg_ear = (left_ear + right_ear) / 2

            # Determine eye state
            is_open = avg_ear > self.EAR_THRESHOLD
            openness = max(0, min(100, (avg_ear - 0.1) / 0.3 * 100))

            # Draw annotations
            cv2.rectangle(
                output_frame,
                (int(left_eye[:, 0].min()), int(left_eye[:, 1].min())),
                (int(left_eye[:, 0].max()), int(left_eye[:, 1].max())),
                (0, 255, 0),
                2,
            )
            cv2.rectangle(
                output_frame,
                (int(right_eye[:, 0].min()), int(right_eye[:, 1].min())),
                (int(right_eye[:, 0].max()), int(right_eye[:, 1].max())),
                (0, 255, 0),
                2,
            )
            cv2.putText(
                output_frame,
                f"Eyes: {'OPEN' if is_open else 'CLOSED'} ({openness:.1f}%)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        return output_frame, is_open, openness
