import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from sklearn.metrics.pairwise import cosine_similarity


class FaceRecognizer:
    def __init__(self):
        # Initialize the face recognition model (InceptionResnetV1 from facenet-pytorch)
        self.mtcnn = MTCNN(keep_all=True)  # Used for face detection
        self.model = InceptionResnetV1(
            pretrained="vggface2"
        ).eval()  # Face recognition model
        self.known_embeddings = []
        self.known_names = []

    def load_known_faces(self, known_faces, known_names):
        """
        Loads known faces and their names into the recognizer.
        """
        for img_path in known_faces:
            img = cv2.imread(img_path)
            if img is None:
                print(f"Failed to load image: {img_path}")
                continue  # Skip the current image if loading fails
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB

            # Detect faces using MTCNN
            faces = self.mtcnn(img_rgb)  # This returns a batch of face tensors

            if faces is not None:
                # If multiple faces are detected, process the first one
                if isinstance(faces, list):
                    faces = faces[0]

                embedding = self.get_embedding(faces)  # Get the face embedding
                self.known_embeddings.append(embedding)

        self.known_names = known_names

    def get_embedding(self, face_img):
        """
        Given a face image, get the embedding using InceptionResnetV1.
        """
        if face_img.ndimension() == 3:  # If a single image, add batch dimension
            face_img = face_img.unsqueeze(0)  # Shape becomes [1, 3, 160, 160]

        face_embedding = self.model(face_img)
        return face_embedding.detach().cpu().numpy()

    def recognize_face(self, face_img):
        """
        Recognizes a face and returns the name and confidence score of the person.
        """
        face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)  # Convert to RGB
        faces = self.mtcnn(face_rgb)  # Detect faces using MTCNN

        if faces is None:  # Handle case when no face is detected
            return "No face detected", 0.0

        # If multiple faces detected, take the first one
        if isinstance(faces, list):
            faces = faces[0]

        # Ensure faces is a batch of tensors (4D: [1, 3, 160, 160])
        if faces.ndimension() == 3:
            faces = faces.unsqueeze(0)

        # Process detected face
        face_embedding = self.get_embedding(faces)
        face_embedding = face_embedding.flatten()  # Ensure 1D

        # Compare with known face embeddings
        similarities = [
            cosine_similarity([face_embedding], [embed.flatten()])[0][0]
            for embed in self.known_embeddings
        ]

        # Identify best match and confidence score
        if similarities:  # Ensure there are known faces to compare with
            best_match_index = np.argmax(similarities)
            confidence = similarities[best_match_index]  # Confidence score

            if confidence > 0.5:  # Recognition threshold
                return self.known_names[best_match_index], confidence

        return "Unknown", 0.0
