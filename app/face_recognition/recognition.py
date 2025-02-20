import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN


class ProductivityRecognizer:
    def __init__(self, known_faces):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.mtcnn = MTCNN(
            keep_all=True,
            device=self.device,
            margin=40,
            min_face_size=40,  # Reduced to detect smaller faces
            thresholds=[0.5, 0.6, 0.6],  # Further lowered thresholds
            post_process=False,
            select_largest=True,  # Prioritize largest face
        )
        self.resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
        self.known_embeddings = []
        self.known_names = []
        self.user_identified = False
        self.identified_user = "Unknown"
        self.load_known_faces(known_faces)

    def load_known_faces(self, face_data):
        print("Loading known faces...")
        for name, path in face_data:
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
            print(f"Loaded {name} embedding, shape: {embedding.shape}")
            self.known_embeddings.append(embedding)
            self.known_names.append(name)
        print(f"Loaded {len(self.known_embeddings)} known faces")
        if not self.known_embeddings:
            print("Warning: No known faces loaded. Recognition will fail.")

    def recognize_user(self, frame):
        # Check frame validity
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
                    if score > 0.9:  # Further lowered threshold to 0.5
                        self.user_identified = True
                        self.identified_user = self.known_names[max_index]
                        print(
                            f"Identified user: {self.identified_user} (score: {score})"
                        )
                        return True
                    else:
                        print(f"Score {score} below threshold (0.5)")
            except Exception as e:
                print(f"Recognition error: {str(e)}")
        else:
            print("No faces detected in frame")
        return False

    def get_identity(self):
        return self.identified_user if self.user_identified else "Unknown"
