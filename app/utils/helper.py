import cv2
import time
from collections import deque


class FPS_counter:
    def __init__(self, window_size=10):
        self.fps_history = deque(maxlen=window_size)
        self.prev_time = time.time()

    def update(self):
        current_time = time.time()
        fps = 1 / (current_time - self.prev_time)
        self.fps_history.append(fps)
        self.prev_time = current_time
        return np.mean(self.fps_history)


def draw_eye_landmarks(frame, landmarks, indices):
    for idx in indices:
        x = int(landmarks[idx][0] * frame.shape[1])
        y = int(landmarks[idx][1] * frame.shape[0])
        cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)


def extract_face_roi(frame, landmarks):
    x_coords = [int(lm[0] * frame.shape[1]) for lm in landmarks]
    y_coords = [int(lm[1] * frame.shape[0]) for lm in landmarks]
    return frame[min(y_coords) : max(y_coords), min(x_coords) : max(x_coords)]
