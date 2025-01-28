from app.client.user_client import UserClient
from app.face_recognition.detection import FaceDetector
from app.face_recognition.recognition import FaceRecognizer


class UserService:
    def __init__(self):
        self.db = UserClient()
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizer()

    def add_employee(self, name: str, image: Image.Image):
        """
        Detect face, generate embedding, and add an employee to the database.
        """
        boxes = self.detector.detect_faces(image)
        if not boxes:
            return "No face detected in the image."

        # Use the first detected face
        cropped_faces = self.detector.crop_faces(image, boxes)
        embedding = self.recognizer.generate_embedding(cropped_faces[0])
        self.db.insert_employee(name, embedding.tolist())
        return f"Employee {name} added successfully."

    def list_employees(self):
        """
        List all employees.
        """
        return self.db.list_employees()

    def delete_employee(self, name: str):
        """
        Delete an employee by name.
        """
        self.db.delete_employee(name)
        return f"Employee {name} deleted successfully."

    def search_employee(self, image: Image.Image):
        """
        Detect face, generate embedding, and search for an employee.
        """
        boxes = self.detector.detect_faces(image)
        if not boxes:
            return {"name": "No face detected", "distance": None}

        # Use the first detected face
        cropped_faces = self.detector.crop_faces(image, boxes)
        embedding = self.recognizer.generate_embedding(cropped_faces[0])
        return self.db.search_employee(embedding)
