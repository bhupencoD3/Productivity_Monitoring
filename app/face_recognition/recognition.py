import cv2
import numpy as np
from facenet_pytorch import InceptionResnetV1, MTCNN
from sklearn.metrics.pairwise import cosine_similarity


class FaceRecognizer:
    def __init__(self):
        # Initialize the face recognition model (InceptionResnetV1 from facenet-pytorch)
        self.mtcnn = MTCNN(keep_all=True)  # Used for face detection
        self.model = InceptionResnetV1(
            pretrained="vggface2"
        ).eval()  # Used for face recognition
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
            faces = self.mtcnn(img_rgb)  # Only one value returned

            if faces is not None:
                for face in faces:
                    embedding = self.get_embedding(face)  # Get the face embedding
                    self.known_embeddings.append(embedding)
        self.known_names = known_names

    def get_embedding(self, face_img):
        """
        Given a face image, get the embedding using InceptionResnetV1.
        """
        # Ensure face_img is a 4D tensor: [batch_size, channels, height, width]
        face_img = face_img.unsqueeze(0)  # Add batch dimension
        face_embedding = self.model(face_img)
        return face_embedding.detach().cpu().numpy()

    def recognize_face(self, face_img):
        """
        Recognizes a face and returns the name of the person.
        """
        face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)  # Convert to RGB
        faces = self.mtcnn(face_rgb)  # Detect faces using MTCNN

        if faces is None or len(faces) == 0:  # Check if faces is None or empty
            return "No face detected"

        # Process the first detected face
        face_embedding = self.get_embedding(faces[0])

        # Flatten the face_embedding to a 1D array
        face_embedding = face_embedding.flatten()

        # Compare the detected face embedding with known face embeddings
        similarities = [
            cosine_similarity([face_embedding], [embed.flatten()])[0][
                0
            ]  # Flatten the known embeddings as well
            for embed in self.known_embeddings
        ]

        best_match_index = np.argmax(similarities)
        name = "Unknown"
        if similarities[best_match_index] > 0.5:  # Threshold for recognizing
            name = self.known_names[best_match_index]
        return name
