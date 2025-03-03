import cv2
import numpy as np
import torch
import datetime
from facenet_pytorch import InceptionResnetV1, MTCNN
from app.dao.employee_dao import EmployeeDAO


class ProductivityRecognizer:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.mtcnn = MTCNN(
            keep_all=True,
            device=self.device,
            margin=40,
            min_face_size=60,  # Increased for better detection in low light
            thresholds=[0.6, 0.7, 0.7],  # Adjusted thresholds
            post_process=False,
            select_largest=True,
        )
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        self.known_embeddings = []
        self.known_names = []
        self.employee_map = {}
        self.user_identified = False
        self.identified_user = "Unknown"
        self.employee_id = None
        self.dao = EmployeeDAO()
        self.load_known_faces()

    def load_known_faces(self):
        print("Loading known faces from database...")
        employees = self.dao.get_all_employees()
        if not employees:
            print("No employees found in database")
            return

        seen_names = set()
        for employee in employees:
            name = employee["name"].lower()
            if name in seen_names:
                print(
                    f"Skipping duplicate name: {name} (employee_id: {employee['employee_id']})"
                )
                continue
            path = employee["face_image_path"]
            employee_id = employee["employee_id"]

            if not path:
                print(f"No face image path for {name} (employee_id: {employee_id})")
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
            embedding = self.resnet(faces[:1]).detach().cpu().numpy()[0]
            embedding = embedding / np.linalg.norm(embedding)  # Normalize embedding
            print(
                f"Loaded {name} embedding, shape: {embedding.shape}, employee_id: {employee_id}, path: {path}"
            )
            self.known_embeddings.append(embedding)
            self.known_names.append(name)
            self.employee_map[name] = employee_id
            seen_names.add(name)

        print(f"Loaded {len(self.known_embeddings)} known faces")
        if not self.known_embeddings:
            print("Warning: No known faces loaded. Recognition will fail.")

    def preprocess_frame(self, frame):
        """
        Adjust brightness and contrast for low-light conditions.
        """
        alpha = 1.5  # Contrast control
        beta = 30  # Brightness control
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    def recognize_user(self, frame):
        if frame is None or frame.size == 0:
            print("Invalid frame received")
            return False

        # Preprocess frame for low-light conditions
        frame = self.preprocess_frame(frame)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.mtcnn(img_rgb)
        num_faces = len(faces) if faces is not None else 0
        print(f"Number of faces detected: {num_faces}")

        if faces is not None and num_faces > 0:
            try:
                for i, face in enumerate(faces):
                    face_np = face.permute(1, 2, 0).cpu().numpy()
                    face_np = (face_np * 255).astype(np.uint8)
                    cv2.imwrite(
                        f"detected_face_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                        face_np,
                    )
                    print(
                        f"Saved detected face to detected_face_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    )

                query_embedding = self.resnet(faces[:1]).detach().cpu().numpy()[0]
                query_embedding = query_embedding / np.linalg.norm(
                    query_embedding
                )  # Normalize
                print(f"Query embedding shape: {query_embedding.shape}")
                similarities = [
                    np.dot(query_embedding, known_embed)
                    for known_embed in self.known_embeddings
                ]
                print(f"Similarity scores: {similarities}")
                for i, score in enumerate(similarities):
                    print(
                        f"Score for {self.known_names[i]} (ID {self.employee_map[self.known_names[i]]}): {score}"
                    )

                if similarities:
                    max_index = np.argmax(similarities)
                    score = similarities[max_index]
                    sorted_scores = sorted(similarities, reverse=True)
                    confidence_gap = (
                        sorted_scores[0] - sorted_scores[1]
                        if len(sorted_scores) > 1
                        else 1.0  # Default gap if only one known face
                    )

                    print(
                        f"Best match: {self.known_names[max_index]} with score {score}, confidence_gap: {confidence_gap}"
                    )
                    if score > 0.92 and confidence_gap > 0.03:
                        self.user_identified = True
                        self.identified_user = self.known_names[max_index]
                        self.employee_id = self.employee_map[self.identified_user]
                        print(
                            f"Identified user: {self.identified_user} (employee_id: {self.employee_id}, score: {score}, confidence_gap: {confidence_gap})"
                        )
                        return True
                    else:
                        print(
                            f"Score {score} below threshold (0.92) or confidence gap {confidence_gap} too small (min 0.03)"
                        )
                        self.user_identified = False
                        self.identified_user = "Unknown"
                        self.employee_id = None
                        return False
            except Exception as e:
                print(f"Recognition error: {str(e)}")
        else:
            print("No faces detected in frame")
        return False

    def get_identity(self):
        return self.identified_user if self.user_identified else "Unknown"

    def get_employee_id(self):
        return self.employee_id if self.user_identified else None
