# face_recognition/recognition.py (Updated with MySQL and Employee IDs)
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from dao.employee_dao import EmployeeDAO  # Import DAO for DB access


class ProductivityRecognizer:
    def __init__(self, known_faces):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.mtcnn = MTCNN(
            keep_all=True,
            device=self.device,
            margin=40,
            min_face_size=40,  # Reduced to detect smaller faces
            thresholds=[0.5, 0.6, 0.6],  # Lowered thresholds
            post_process=False,
            select_largest=True,  # Prioritize largest face
        )
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        self.known_embeddings = []
        self.known_names = []
        self.employee_map = {}  # Map name to employee_id
        self.user_identified = False
        self.identified_user = "Unknown"
        self.employee_id = None  # Store the identified employee's ID
        self.dao = EmployeeDAO()  # Initialize DAO
        self.load_known_faces(known_faces)

    def load_known_faces(self, face_data):
        """
        Load known faces into memory and store them in the employees table.
        """
        print("Loading known faces...")
        for name, path in face_data:
            # Add employee to database if not already present
            employee_id = self.dao.add_employee(name, face_image_path=path)
            if employee_id is None:
                print(f"Failed to add {name} to database")
                continue

            img = cv2.imread(path)
            if img is None:
                print(f"Failed to load image: {path}")
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.mtcnn(img_rgb)
            if faces is None or len(faces) == 0:
                print(f"No faces detected in {path}")
                continue
            embedding = (
                self.resnet(faces[:1]).detach().cpu().numpy()[0]
            )  # First face only
            print(
                f"Loaded {name} embedding, shape: {embedding.shape}, employee_id: {employee_id}"
            )
            self.known_embeddings.append(embedding)
            self.known_names.append(name)
            self.employee_map[name] = employee_id  # Map name to employee_id

        print(f"Loaded {len(self.known_embeddings)} known faces")
        if not self.known_embeddings:
            print("Warning: No known faces loaded. Recognition will fail.")

    def recognize_user(self, frame):
        """
        Recognize a user from a frame and set identified_user and employee_id.
        """
        if frame is None or frame.size == 0:
            print("Invalid frame received")
            return False

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.mtcnn(img_rgb)
        num_faces = len(faces) if faces is not None else 0
        print(f"Number of faces detected: {num_faces}")

        if faces is not None and num_faces > 0:
            try:
                # Visualize detected face (for debugging)
                for i, face in enumerate(faces):
                    face_np = face.permute(1, 2, 0).cpu().numpy()
                    face_np = (face_np * 255).astype(np.uint8)
                    cv2.imshow(f"Detected Face {i}", face_np)

                query_embedding = (
                    self.resnet(faces[:1]).detach().cpu().numpy()[0]
                )  # First face
                print(f"Query embedding shape: {query_embedding.shape}")
                similarities = [
                    np.dot(query_embedding, known_embed)
                    / (np.linalg.norm(query_embedding) * np.linalg.norm(known_embed))
                    for known_embed in self.known_embeddings
                ]
                print(f"Similarity scores: {similarities}")
                if similarities:
                    max_index = np.argmax(similarities)
                    score = similarities[max_index]
                    print(
                        f"Best match: {self.known_names[max_index]} with score {score}"
                    )
                    if score > 0.8:  # Adjust threshold as needed
                        self.user_identified = True
                        self.identified_user = self.known_names[max_index]
                        self.employee_id = self.employee_map[self.identified_user]
                        print(
                            f"Identified user: {self.identified_user} (employee_id: {self.employee_id}, score: {score})"
                        )
                        return True
                    else:
                        print(f"Score {score} below threshold (0.8)")
            except Exception as e:
                print(f"Recognition error: {str(e)}")
        else:
            print("No faces detected in frame")
        return False

    def get_identity(self):
        """
        Return the identified user's name.
        """
        return self.identified_user if self.user_identified else "Unknown"

    def get_employee_id(self):
        """
        Return the identified employee's ID.
        """
        return self.employee_id if self.user_identified else None

