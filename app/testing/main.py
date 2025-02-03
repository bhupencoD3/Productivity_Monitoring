import cv2
from detection import EyeStateDetector


class WebcamApp:
    def __init__(self):
        self.detector = EyeStateDetector()
        self.running = False

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not access webcam")
            return

        print("Starting webcam... Press 'Q' to quit")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # Mirror frame and process
            frame = cv2.flip(frame, 1)
            processed_frame, is_open, openness = self.detector.detect(frame)

            # Display frame
            cv2.imshow("Eye State Monitor", processed_frame)

            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.running = False

        cap.release()
        cv2.destroyAllWindows()
        print("Application closed")


if __name__ == "__main__":
    app = WebcamApp()
    app.run()
